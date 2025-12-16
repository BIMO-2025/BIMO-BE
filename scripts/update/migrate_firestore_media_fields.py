"""
Firestore 이미지/프로필 사진 필드 마이그레이션 스크립트

목표
- reviews: imageUrl(단수) -> imageUrls(복수 리스트)로 통일하고, 타입/빈값/개수 제한 정리
- users: 프로필 사진 필드를 photo_url로 통일 (구버전 photoUrl/photoURL 등이 있으면 이관)

기본 동작은 dry-run(변경 없음)이며, --commit 옵션을 주면 실제로 Firestore를 업데이트합니다.
"""

from __future__ import annotations

import argparse
import os
import sys
import base64
import io
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

# scripts/update/ 아래에서 실행해도 레포 루트의 `app/` 패키지를 import 할 수 있도록 경로 보정
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


def _looks_like_http_url(s: str) -> bool:
    return s.startswith("http://") or s.startswith("https://")


def _looks_like_data_image_url(s: str) -> bool:
    return s.startswith("data:image/")


def _bytes_to_jpeg_base64_data_url(
    raw: bytes,
    *,
    max_size: tuple[int, int] = (800, 800),
    quality: int = 85,
    max_base64_chars: int = 700 * 1024,  # 기존 uploads 라우터와 동일(문자 수 기준)
) -> str:
    """
    이미지 바이트를 JPEG로 압축 후 Base64 Data URL(data:image/jpeg;base64,...)로 변환합니다.
    """
    from PIL import Image

    image = Image.open(io.BytesIO(raw))

    # RGBA/LA/P -> RGB (투명 배경 흰색 처리)
    if image.mode in ("RGBA", "LA", "P"):
        background = Image.new("RGB", image.size, (255, 255, 255))
        if image.mode == "P":
            image = image.convert("RGBA")
        if image.mode == "RGBA":
            background.paste(image, mask=image.split()[-1])
        else:
            background.paste(image)
        image = background
    elif image.mode != "RGB":
        image = image.convert("RGB")

    image.thumbnail(max_size, Image.Resampling.LANCZOS)

    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=quality, optimize=True)
    jpeg_bytes = buf.getvalue()

    b64 = base64.b64encode(jpeg_bytes).decode("utf-8")
    data_url = f"data:image/jpeg;base64,{b64}"

    if len(data_url) > max_base64_chars:
        raise ValueError(
            f"Base64 Data URL이 너무 큽니다: {len(data_url) // 1024}KB (limit {max_base64_chars // 1024}KB)"
        )

    return data_url


def _clean_str(value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return None
    v = value.strip()
    return v or None


def _clean_str_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []
    out: List[str] = []
    for item in value:
        s = _clean_str(item)
        if s:
            out.append(s)
    return out


def _dedupe_keep_order(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for x in items:
        if x in seen:
            continue
        seen.add(x)
        out.append(x)
    return out


@dataclass
class ReviewMigrationResult:
    should_update: bool
    update_data: Dict[str, Any]
    reason: str


def build_review_update(
    doc: Dict[str, Any],
    *,
    delete_field_sentinel: Any,
    ensure_image_urls_field: bool,
    max_images: int,
) -> ReviewMigrationResult:
    """
    reviews 문서 1개에 대해 업데이트(필요 시) 내용을 계산합니다.
    """
    before_image_urls = doc.get("imageUrls", None)
    before_image_url = doc.get("imageUrl", None)

    image_urls = _clean_str_list(before_image_urls)
    image_url = _clean_str(before_image_url)

    if (not image_urls) and image_url:
        image_urls = [image_url]

    image_urls = _dedupe_keep_order(image_urls)[:max_images]

    update: Dict[str, Any] = {}
    reasons: List[str] = []

    # imageUrls 정규화
    if ensure_image_urls_field:
        # 항상 리스트 필드가 존재하도록 (없거나 타입이 틀리면) 업데이트
        if before_image_urls is None or not isinstance(before_image_urls, list):
            update["imageUrls"] = image_urls
            reasons.append("ensure_imageUrls(list)")
        else:
            # 값 자체가 달라진 경우만 업데이트
            cleaned_before = _dedupe_keep_order(_clean_str_list(before_image_urls))[:max_images]
            if cleaned_before != image_urls:
                update["imageUrls"] = image_urls
                reasons.append("normalize_imageUrls")
    else:
        # ensure 하지 않으면, 실제 변화가 있을 때만 업데이트
        cleaned_before = _dedupe_keep_order(_clean_str_list(before_image_urls))[:max_images]
        if cleaned_before != image_urls:
            update["imageUrls"] = image_urls
            reasons.append("normalize_imageUrls")

    # imageUrl(단수) 제거 (있으면)
    if "imageUrl" in doc:
        update["imageUrl"] = delete_field_sentinel
        reasons.append("delete_imageUrl")

    if not update:
        return ReviewMigrationResult(False, {}, "no_change")

    return ReviewMigrationResult(True, update, ",".join(reasons))


@dataclass
class UserMigrationResult:
    should_update: bool
    update_data: Dict[str, Any]
    reason: str


def build_user_update(
    doc: Dict[str, Any],
    *,
    delete_field_sentinel: Any,
) -> UserMigrationResult:
    """
    users 문서 1개에 대해 업데이트(필요 시) 내용을 계산합니다.
    """
    # 표준 키
    std = _clean_str(doc.get("photo_url"))

    # 구버전 후보 키들
    candidates = [
        ("photoUrl", _clean_str(doc.get("photoUrl"))),
        ("photoURL", _clean_str(doc.get("photoURL"))),
        ("photo", _clean_str(doc.get("photo"))),
        ("picture", _clean_str(doc.get("picture"))),
    ]

    chosen = std
    if not chosen:
        for _, v in candidates:
            if v:
                chosen = v
                break

    update: Dict[str, Any] = {}
    reasons: List[str] = []

    # photo_url 트림/이관
    if chosen and chosen != std:
        update["photo_url"] = chosen
        reasons.append("set_photo_url")
    elif std and isinstance(doc.get("photo_url"), str) and doc.get("photo_url") != std:
        # 공백 포함 등으로 트림이 필요한 케이스
        update["photo_url"] = std
        reasons.append("trim_photo_url")

    # 구버전 키 제거 (있으면)
    for key, v in candidates:
        if key in doc:
            update[key] = delete_field_sentinel
            reasons.append(f"delete_{key}")

    if not update:
        return UserMigrationResult(False, {}, "no_change")
    return UserMigrationResult(True, update, ",".join(reasons))


def _batched(iterable: Iterable[Any], size: int) -> Iterable[List[Any]]:
    batch: List[Any] = []
    for item in iterable:
        batch.append(item)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


def main() -> int:
    parser = argparse.ArgumentParser(description="Firestore 이미지/프로필 사진 필드 마이그레이션")
    parser.add_argument("--commit", action="store_true", help="실제로 Firestore에 반영합니다 (기본: dry-run)")
    parser.add_argument("--limit", type=int, default=0, help="최대 처리 문서 수(0이면 무제한)")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=400,
        help="Firestore batch commit 단위 (기본 400; Firestore 제한 500 미만 권장)",
    )
    parser.add_argument("--max-images", type=int, default=3, help="리뷰 이미지 최대 개수 (기본 3)")
    parser.add_argument(
        "--convert-http-urls",
        action="store_true",
        help="reviews.imageUrls에 https/http URL이 있으면 내려받아 Base64 Data URL로 변환해 저장합니다.",
    )
    parser.add_argument(
        "--convert-user-photo-url",
        action="store_true",
        help="users.photo_url이 https/http URL이면 내려받아 Base64 Data URL로 변환해 저장합니다.",
    )
    parser.add_argument("--http-timeout", type=float, default=20.0, help="이미지 다운로드 타임아웃(초)")
    parser.add_argument(
        "--max-total-image-chars",
        type=int,
        default=900 * 1024,
        help="리뷰 문서의 imageUrls 문자열 총합 상한(대략 Firestore 1MB 제한 회피용, 기본 900KB)",
    )
    parser.add_argument(
        "--no-ensure-imageurls",
        action="store_true",
        help="imageUrls 필드를 모든 리뷰 문서에 강제로 만들지 않습니다(변화가 있는 문서만 업데이트).",
    )
    args = parser.parse_args()

    # Firebase 초기화 (env: FIREBASE_SERVICE_ACCOUNT_KEY 필요)
    from app.core.firebase import get_firebase_service
    from firebase_admin import firestore as admin_firestore

    firebase_service = get_firebase_service()
    firebase_service.initialize()
    db = firebase_service.db

    delete_field = admin_firestore.DELETE_FIELD

    ensure_image_urls = not args.no_ensure_imageurls
    convert_http_urls = bool(args.convert_http_urls)
    convert_user_photo_url = bool(args.convert_user_photo_url)

    print("=== Firestore Media Fields Migration ===")
    print(f"- mode: {'COMMIT' if args.commit else 'DRY-RUN'}")
    print(f"- limit: {args.limit or 'unlimited'}")
    print(f"- batch_size: {args.batch_size}")
    print(f"- max_images: {args.max_images}")
    print(f"- ensure_imageUrls_field: {ensure_image_urls}")
    print(f"- convert_http_urls: {convert_http_urls}")
    print(f"- convert_user_photo_url: {convert_user_photo_url}")
    print("")

    # -------------------------------------------------------------------------
    # reviews 마이그레이션
    # -------------------------------------------------------------------------
    reviews_ref = db.collection("reviews")
    users_ref = db.collection("users")

    updated_reviews = 0
    scanned_reviews = 0

    review_ops: List[Tuple[Any, Dict[str, Any], str]] = []

    print("[1/2] reviews 컬렉션 마이그레이션 중...")
    http_client = None
    if convert_http_urls or convert_user_photo_url:
        import httpx

        http_client = httpx.Client(
            timeout=args.http_timeout,
            follow_redirects=True,
            headers={
                "User-Agent": "BIMO-BE migration script",
                "Accept": "image/*,*/*;q=0.8",
            },
        )

    converted_images = 0
    download_errors = 0
    for doc_snap in reviews_ref.stream():
        scanned_reviews += 1
        doc = doc_snap.to_dict() or {}

        result = build_review_update(
            doc,
            delete_field_sentinel=delete_field,
            ensure_image_urls_field=ensure_image_urls,
            max_images=args.max_images,
        )

        # 옵션: reviews.imageUrls 내 http(s) URL -> base64 data URL로 변환해 저장
        if convert_http_urls:
            current = doc.get("imageUrls") or []
            if isinstance(current, str):
                current = [current]
            current_clean = _dedupe_keep_order(_clean_str_list(current))[: args.max_images]

            if any(_looks_like_http_url(u) for u in current_clean):
                converted_list: List[str] = []
                for u in current_clean:
                    if _looks_like_data_image_url(u):
                        converted_list.append(u)
                        continue
                    if _looks_like_http_url(u):
                        try:
                            if http_client is None:
                                raise RuntimeError("http client is not initialized")
                            resp = http_client.get(u)
                            resp.raise_for_status()
                            data_url = _bytes_to_jpeg_base64_data_url(resp.content)
                            converted_images += 1
                            converted_list.append(data_url)
                        except Exception:
                            download_errors += 1
                            converted_list.append(u)
                    else:
                        converted_list.append(u)

                # Firestore 문서 크기 제한 회피: 문자열 총합이 너무 크면 뒤에서부터 잘라냄
                while sum(len(x) for x in converted_list) > args.max_total_image_chars and converted_list:
                    converted_list.pop()

                if converted_list != current_clean:
                    merged = dict(result.update_data)
                    merged["imageUrls"] = converted_list
                    reason = result.reason if result.reason != "no_change" else ""
                    reason = (reason + ",convert_http_urls").strip(",") or "convert_http_urls"
                    result = ReviewMigrationResult(True, merged, reason)
        if result.should_update:
            review_ops.append((doc_snap.reference, result.update_data, result.reason))
            updated_reviews += 1

        if args.limit and scanned_reviews >= args.limit:
            break

    print(f"  - scanned: {scanned_reviews}")
    print(f"  - to_update: {updated_reviews}")
    if convert_http_urls:
        print(f"  - converted_images: {converted_images}")
        print(f"  - download_errors: {download_errors}")

    if args.commit and review_ops:
        print("  - committing review updates...")
        for chunk in _batched(review_ops, args.batch_size):
            batch = db.batch()
            for ref, update_data, _ in chunk:
                batch.update(ref, update_data)
            batch.commit()
        print("  - review updates committed.")
    else:
        # dry-run: 샘플 출력
        for ref, update_data, reason in review_ops[:5]:
            print(f"  - sample update ({reason}): {ref.path} -> {list(update_data.keys())}")

    print("")

    # -------------------------------------------------------------------------
    # users 마이그레이션
    # -------------------------------------------------------------------------
    updated_users = 0
    scanned_users = 0

    user_ops: List[Tuple[Any, Dict[str, Any], str]] = []

    print("[2/2] users 컬렉션 마이그레이션 중...")
    converted_user_photos = 0
    user_photo_errors = 0
    for doc_snap in users_ref.stream():
        scanned_users += 1
        doc = doc_snap.to_dict() or {}

        result = build_user_update(doc, delete_field_sentinel=delete_field)

        # 옵션: users.photo_url이 http(s) URL이면 base64 data URL로 변환해 저장
        if convert_user_photo_url:
            current_photo = _clean_str(doc.get("photo_url"))
            if current_photo and _looks_like_http_url(current_photo):
                try:
                    if http_client is None:
                        raise RuntimeError("http client is not initialized")
                    resp = http_client.get(current_photo)
                    resp.raise_for_status()
                    data_url = _bytes_to_jpeg_base64_data_url(resp.content)
                    converted_user_photos += 1
                    merged = dict(result.update_data)
                    merged["photo_url"] = data_url
                    reason = result.reason if result.reason != "no_change" else ""
                    reason = (reason + ",convert_user_photo_url").strip(",") or "convert_user_photo_url"
                    result = UserMigrationResult(True, merged, reason)
                except Exception:
                    user_photo_errors += 1
        if result.should_update:
            user_ops.append((doc_snap.reference, result.update_data, result.reason))
            updated_users += 1

        if args.limit and scanned_users >= args.limit:
            break

    print(f"  - scanned: {scanned_users}")
    print(f"  - to_update: {updated_users}")
    if convert_user_photo_url:
        print(f"  - converted_user_photos: {converted_user_photos}")
        print(f"  - download_errors: {user_photo_errors}")

    if args.commit and user_ops:
        print("  - committing user updates...")
        for chunk in _batched(user_ops, args.batch_size):
            batch = db.batch()
            for ref, update_data, _ in chunk:
                batch.update(ref, update_data)
            batch.commit()
        print("  - user updates committed.")
    else:
        for ref, update_data, reason in user_ops[:5]:
            print(f"  - sample update ({reason}): {ref.path} -> {list(update_data.keys())}")

    print("")
    print("=== DONE ===")
    print(f"reviews: scanned={scanned_reviews}, updated={updated_reviews}")
    print(f"users:   scanned={scanned_users}, updated={updated_users}")
    print("")
    print("TIP: 실제 반영은 --commit 옵션을 사용하세요.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


