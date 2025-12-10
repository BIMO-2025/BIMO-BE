# 공항 검색 알고리즘 설계 문서

## 개요
한국 사용자를 위한 한글/영어 이중 언어 공항 검색 알고리즘입니다.

## 알고리즘 설계

### 1. 데이터 구조 설계

각 공항 데이터는 다음과 같은 다중 언어 필드를 포함합니다:

```python
{
    "code": "ICN",                    # IATA 공항 코드 (검색 키)
    "name": "인천국제공항 (Incheon International Airport)",  # 통합 이름
    "name_en": "Incheon International Airport",  # 영어 이름
    "name_ko": "인천국제공항",         # 한글 이름
    "city": "인천 (Incheon)",         # 통합 도시명
    "city_en": "Incheon",             # 영어 도시명
    "city_ko": "인천",                # 한글 도시명
    "country": "대한민국 (South Korea)",  # 통합 국가명
    "country_en": "South Korea",      # 영어 국가명
    "country_ko": "대한민국",         # 한글 국가명
}
```

### 2. 검색 알고리즘

#### 2.1 다중 필드 검색 (Multi-field Search)
모든 검색 가능한 필드를 검색 대상으로 포함합니다.

**검색 대상 필드:**
- `name`, `name_en`, `name_ko` - 공항 이름 (3개 필드)
- `city`, `city_en`, `city_ko` - 도시명 (3개 필드)
- `country`, `country_en`, `country_ko` - 국가명 (3개 필드)
- `code` - IATA 공항 코드 (1개 필드)

**총 10개 필드에서 동시 검색**

#### 2.2 부분 일치 검색 (Substring Matching)
- **방식**: 대소문자 무시 부분 문자열 검색
- **알고리즘**: `query.lower() in field.lower()`
- **예시**:
  - "인" → "인천", "인도네시아" 모두 매칭
  - "new" → "New York", "New Zealand" 모두 매칭

#### 2.3 다중 언어 지원
- **한글 검색**: `name_ko`, `city_ko`, `country_ko` 필드 검색
- **영어 검색**: `name_en`, `city_en`, `country_en` 필드 검색
- **통합 검색**: `name`, `city`, `country` (한글+영어 결합) 필드 검색
- **코드 검색**: `code` 필드 (대소문자 무시)

#### 2.4 검색 알고리즘 의사코드

```python
async def search_destinations(query: str) -> List[Airport]:
    """
    공항 검색 알고리즘
    """
    if not query:
        return []
    
    # 1. 쿼리 정규화 (소문자 변환)
    q = query.lower()
    
    # 2. Firestore에서 모든 공항 문서 조회
    docs = collection.stream()
    
    results = []
    
    for doc in docs:
        data = doc.to_dict()
        
        # 3. 검색 가능한 모든 필드 리스트 생성
        searchable_fields = [
            data.get("name", ""),
            data.get("name_en", ""),
            data.get("name_ko", ""),
            data.get("city", ""),
            data.get("city_en", ""),
            data.get("city_ko", ""),
            data.get("country", ""),
            data.get("country_en", ""),
            data.get("country_ko", ""),
            data.get("code", ""),
        ]
        
        # 4. 부분 일치 검색 (하나라도 매칭되면 결과에 추가)
        if any(q in field.lower() for field in searchable_fields if field):
            results.append(Airport(**data))
    
    return results
```

### 3. 검색 예시

#### 예시 1: 한글 검색
```
입력: "인천"
검색 필드: name_ko, city_ko, country_ko, name, city, country
결과: 인천국제공항 (ICN)
```

#### 예시 2: 영어 검색
```
입력: "New York"
검색 필드: name_en, city_en, country_en, name, city, country
결과: 존 F. 케네디 국제공항 (JFK) - "New York" 도시로 매칭
```

#### 예시 3: 공항 코드 검색
```
입력: "icn"
검색 필드: code (대소문자 무시)
결과: 인천국제공항 (ICN)
```

#### 예시 4: 국가명 검색
```
입력: "미국"
검색 필드: country_ko, country, city_ko, city
결과: JFK, LAX, ORD, ATL 등 미국의 모든 공항
```

### 4. 알고리즘 특징

#### 장점
1. **유연한 검색**: 한글/영어/코드 모두 지원
2. **부분 일치**: 정확한 입력이 아니어도 검색 가능
3. **다중 필드**: 이름, 도시, 국가 모든 필드 검색
4. **대소문자 무시**: 사용자 편의성 향상

#### 단점 및 개선 방안
1. **성능**: 전체 문서 스캔 (현재는 데이터가 적어서 문제 없음)
   - **개선**: Firestore 인덱싱 + Algolia/Elasticsearch 도입
2. **정확도**: 부분 일치로 인한 노이즈 결과
   - **개선**: 우선순위 점수 시스템 도입 (정확 일치 > 부분 일치)
3. **자모 분리**: 한글 자모 분리 검색 미지원
   - **개선**: 한글 초성 검색 라이브러리 도입

### 5. 향후 개선 방안

#### 5.1 우선순위 기반 검색
```python
def calculate_score(query: str, data: dict) -> int:
    score = 0
    
    # 정확 일치 (최우선)
    if query.lower() == data.get("code", "").lower():
        score += 100
    
    # 이름 정확 일치
    if query.lower() == data.get("name_ko", "").lower():
        score += 90
    
    # 이름 시작 일치
    if data.get("name_ko", "").startswith(query):
        score += 50
    
    # 부분 일치
    if query in data.get("name_ko", ""):
        score += 10
    
    return score

# 점수 순으로 정렬
results.sort(key=lambda x: calculate_score(query, x), reverse=True)
```

#### 5.2 풀텍스트 검색 엔진 도입
- **Algolia**: 빠른 검색, 한글 지원
- **Elasticsearch**: 강력한 검색 기능
- **Firestore Text Search**: Firestore 확장 기능

#### 5.3 자동완성 지원
```python
# 입력: "인" → ["인천", "인도네시아", "인천국제공항"]
async def autocomplete(query: str, limit: int = 5):
    results = await search_destinations(query)
    return results[:limit]  # 상위 5개만 반환
```

### 6. 현재 구현 상태

✅ **구현 완료**:
- 다중 언어 필드 검색
- 부분 일치 검색
- 대소문자 무시 검색
- 한글/영어/코드 통합 검색

⏳ **향후 구현**:
- 우선순위 점수 시스템
- 검색 결과 정렬
- 자동완성 API
- 검색 성능 최적화

## 사용 예시

```python
# 한글 검색
GET /destinations/search?query=인천
→ 인천국제공항 (ICN)

# 영어 검색
GET /destinations/search?query=Incheon
→ 인천국제공항 (ICN)

# 국가 검색
GET /destinations/search?query=미국
→ JFK, LAX, ORD, ATL, SFO, MIA, SEA, DFW, LAS, BOS 등

# 코드 검색
GET /destinations/search?query=ICN
→ 인천국제공항 (ICN)
```





