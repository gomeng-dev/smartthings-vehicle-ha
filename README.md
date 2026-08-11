# 스마트싱스 차량

[![GitHub release](https://img.shields.io/github/v/release/qn1213/smartthings-vehicle-ha?display_name=tag)](https://github.com/qn1213/smartthings-vehicle-ha/releases)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)
[![CI](https://github.com/qn1213/smartthings-vehicle-ha/actions/workflows/ci.yml/badge.svg)](https://github.com/qn1213/smartthings-vehicle-ha/actions/workflows/ci.yml)

한국 SmartThings에 등록된 현대자동차·기아·제네시스 차량을 Home Assistant에서 조회하고 제어하는 커스텀 통합입니다. 내연기관·하이브리드·플러그인 하이브리드 차량과 함께 2025년식 아이오닉 5를 기준으로 전기차 상태 조회를 지원합니다.

Home Assistant 공식 SmartThings 통합의 OAuth 인증을 재사용하므로, 별도 토큰을 복사하거나 붙여 넣을 필요가 없습니다.

## 주요 기능

- SmartThings 차량 자동 탐색
- 주행 가능 거리, 누적 주행 거리, 시동, 공조, 잠금, 도어, 창문, 연결 상태 조회
- 전기차 고전압 배터리 잔량, 충전 상태·방식, 충전 커넥터 상태, 보조 배터리·고전압 배터리 경고 조회
- 연료, 타이어 공기압, 외장 램프 회로, 스마트키 배터리, 워셔액, 브레이크액, 엔진오일 경고 조회
- 실차가 제공하면 네 바퀴별 공기압 경고, 현재 공조 풍량과 김서림 제거 상태 조회
- 차량 상태 새로고침 및 연결 확인
- 차량 잠금 / 잠금 해제는 잠금 엔티티로 제어
- SmartThings 앱처럼 원격 시동은 별도 스위치로 노출하지 않고 공조 켜기 / 끄기 스위치로 함께 관리
- Google Assistant에서 에어컨처럼 다루기 쉬운 냉방 모드 climate 엔티티 제공
- 공조 온도, 작동 시간, 앞유리 김서림 제거 설정

## 지원 환경

- Home Assistant 2024.12.0 이상
- HACS
- Home Assistant 공식 SmartThings 통합
- 한국 SmartThings 계정에 등록된 현대자동차·기아·제네시스 차량
- 전기차 상태 조회는 2025년식 현대 아이오닉 5의 SmartThings `vehicleBattery` capability를 기준으로 구현

## 현대자동차 공개 API 대응 범위

[Hyundai Developers 데이터 API](https://developers.hyundai.com/web/v1/hyundai/data_api)에 공개된 차량 상태 항목을 실차 SmartThings capability와 대조해 반영합니다.

- 주행 가능 거리와 누적 운행 거리
- 전기차 충전 상태, 배터리 잔량, 충전기 연결 종류
- 주유, 타이어 공기압, 외장 램프 회로, 스마트키 배터리, 워셔액, 브레이크액, 엔진오일 경고

이 통합은 Hyundai Developers 서버를 직접 호출하지 않고 SmartThings 차량 장치가 전달한 데이터만 사용합니다. 따라서 커넥티드 서비스 가입일·무료 종료일, 목표 충전량처럼 SmartThings 프로필에 없는 값은 만들지 않습니다. 계정 인증·개인정보 제공 동의·철회·데이터 삭제 콜백은 서비스 사업자용 API라 Home Assistant 차량 엔티티 대상이 아닙니다. 실제 차량에서 정상 값을 받지 못한 제조사·모델·연식·트림·색상·차량 번호와 요청에 따라 충전 남은 시간은 노출하지 않습니다.

## Home Assistant 표시 분류

엔티티 이름이 같은 카테고리끼리 정렬되도록 다음 접두어를 사용합니다.

- `주행 ·`: 주행 가능 거리, 누적 주행 거리
- `차량 상태 ·`: 시동, 잠금, 도어, 창문
- `공조 ·`: 공조 상태, 팬 속도, 실내 온도, 김서림 제거 상태
- `전기차 ·`: 고전압 배터리 잔량, 충전 상태·방식·커넥터
- `경고 ·`: 배터리, 타이어, 오일과 각종 소모품 경고
- `시스템 ·`: 연결 상태, 명령 상태와 점검 버튼

잠금·공조·점검 버튼은 최상단 제어 영역에, 공조 설정 엔티티는 그다음 `설정` 영역에, 모든 조회 센서는 맨 아래 `진단` 영역에 표시됩니다. 현재 사용하는 엔티티 ID와 고유 ID는 변경하지 않아 기존 자동화에는 영향을 주지 않습니다.

업데이트 전에 생성된 제조사·모델·연식·트림·색상·차량 번호·충전 남은 시간 엔티티는 통합을 다시 불러오거나 Home Assistant를 재시작할 때 엔티티 레지스트리에서도 자동으로 삭제됩니다.

## 설치 전 준비

먼저 Home Assistant에 공식 SmartThings 통합을 설정하세요.

1. Home Assistant → 설정 → 기기 및 서비스
2. 통합 추가 → SmartThings
3. 삼성 계정 로그인 및 권한 승인
4. SmartThings 앱 또는 Home Assistant에서 차량이 계정에 등록되어 있는지 확인

## HACS 설치

아직 HACS 기본 저장소에 포함되지 않은 경우 사용자 정의 저장소로 추가합니다.

1. HACS → 통합
2. 우측 상단 메뉴 → 사용자 정의 저장소
3. 저장소 URL 입력

   ```text
   https://github.com/qn1213/smartthings-vehicle-ha
   ```

4. 카테고리 `Integration` 선택
5. `스마트싱스 차량` 다운로드
6. Home Assistant 재시작

## 최초 설정

Home Assistant를 재시작한 뒤 통합을 추가합니다.

1. 설정 → 기기 및 서비스
2. 통합 추가
3. `스마트싱스 차량` 검색
4. 자동 탐색된 차량 목록에서 차량 선택
5. 차량 이름 확인 또는 수정
6. 설정 완료

자동 탐색된 차량이 없으면 SmartThings 차량 장치 ID를 직접 입력할 수 있습니다.

## 생성되는 엔티티

### 센서

- 주행 가능 거리
- 누적 주행 거리
- 시동 상태
- 공조 상태
- 실내 온도
- 잠금 상태
- 운전석 / 조수석 / 뒤 좌측 / 뒤 우측 도어
- 운전석 / 조수석 / 뒤 좌측 / 뒤 우측 창문
- 연료 경고
- 스마트키 배터리 경고
- 타이어 공기압 경고와 네 바퀴별 공기압 경고
- 외장 램프 회로, 워셔액, 브레이크액, 엔진오일 경고
- 공조 풍량과 김서림 제거 상태
- 고전압 배터리 잔량(전기차)
- 충전 상태와 충전 방식(전기차)
- 충전 커넥터 상태(전기차)
- 보조 배터리 경고와 고전압 배터리 경고(지원 차량)
- 연결 상태

전기차 전용 센서는 차량이 해당 SmartThings attribute를 제공할 때만 생성됩니다. 차량 사양, Bluelink/커넥티드 서비스 상태와 SmartThings 장치 프로필에 따라 일부 센서는 표시되지 않을 수 있습니다.

### 버튼

- 차량 상태 새로고침
- 차량 연결 확인

### 잠금

- 차량 잠금: 잠금 / 잠금 해제

### 스위치

- 공조: 켜기 / 끄기. 켜기 명령에는 설정된 작동 시간이 포함되어 SmartThings 차량 원격 공조처럼 시동과 공조가 함께 동작합니다.
- 앞유리 김서림 제거: 켜기 / 끄기. 이 값은 다음 공조 켜기 명령에 함께 전송됩니다.

### 에어컨

- 에어컨: Google Assistant에서 온도 설정과 공조 켜기 / 끄기를 자연스럽게 제어하기 위한 냉방 모드 climate 엔티티입니다.

### 공조 설정

- 공조 설정 온도: 17–27℃, 기본 22℃
- 공조 작동 시간: 1–30분, 기본 10분
- 앞유리 김서림 제거: `off` / `on`, 기본 `off`

`공조` 스위치를 켜면 현재 설정된 공조 값과 작동 시간이 SmartThings로 전송됩니다. 온도나 작동 시간을 바꾸는 것만으로는 차량 명령이 실행되지 않습니다.

Google Assistant에는 `climate.smartthings_vehicle_hvac`를 `쏘나타 에어컨`으로 노출하는 것을 권장합니다. 추가 옵션으로 `switch.smartthings_vehicle_hvac_defog`, `select.smartthings_vehicle_hvac_ignition_duration`를 함께 노출하면 음성으로 온도 설정, 에어컨 켜기/끄기, 김서림 제거 설정, 작동 시간 설정을 다루기 쉽습니다.

## 안전 안내

차량 제어는 실제 차량 상태를 바꾸는 동작입니다.

- 잠금 해제와 공조 제어는 신중하게 사용하세요. 공조 켜기는 차량 원격 공조 동작으로, 설정된 작동 시간 동안 차량 시동/공조가 함께 동작할 수 있습니다.
- 자동화에 차량 제어를 넣을 때는 위치, 시간, 재실 여부 등 안전 조건을 함께 설정하는 것을 권장합니다.
- 설치 및 설정 과정에서는 차량 제어 명령이 자동으로 실행되지 않습니다.
- 창문은 현재 상태 조회만 지원합니다. SmartThings capability에 창문 열기/닫기 명령이 제공되지 않아 제어 버튼을 만들지 않습니다.
- 전기차 충전 시작·중지 명령은 차량과 충전 환경에 영향을 줄 수 있어 현재 버전에서는 제공하지 않으며 상태 조회만 지원합니다.

## 문제 해결

### SmartThings 차량 통합이 검색되지 않음

- HACS 설치 후 Home Assistant를 재시작했는지 확인하세요.
- `custom_components/smartthings_vehicle` 경로에 통합 파일이 설치되었는지 확인하세요.

### SmartThings에 연결할 수 없다는 오류가 표시됨

- 공식 SmartThings 통합이 먼저 설정되어 있어야 합니다.
- 공식 SmartThings 통합의 삼성 계정 로그인이 만료되지 않았는지 확인하세요.
- Home Assistant를 재시작한 뒤 다시 시도하세요.

### 차량이 자동 탐색되지 않음

- SmartThings 앱에서 차량이 같은 삼성 계정에 등록되어 있는지 확인하세요.
- 공식 SmartThings 통합이 해당 계정으로 로그인되어 있는지 확인하세요.
- 필요한 경우 SmartThings 차량 장치 ID를 직접 입력하세요.

### 차량 capability 진단 정보 다운로드

시트 열선·통풍처럼 차량별 SmartThings capability를 확인해야 할 때 사용할 수 있습니다.

1. Home Assistant → 설정 → 기기 및 서비스 → `스마트싱스 차량`
2. 통합 카드 또는 차량 기기의 `⋮` 메뉴 선택
3. `진단 정보 다운로드` 선택

진단 파일은 장치 ID, 위치 ID, VIN, 번호판과 일반 차량 상태 값을 제외합니다. 시트·열선·통풍·공조 관련 값과 component/capability/attribute 구조, 조회 가능한 capability 명령 스키마만 포함합니다. 공유하기 전에는 파일 내용을 한 번 더 확인하세요.

### 버튼/토글을 눌러도 차량 상태가 바로 바뀌지 않음

SmartThings 차량 명령은 네트워크, 차량 통신 상태, 제조사 서버 상태에 따라 반영까지 시간이 걸릴 수 있습니다. 이 통합은 잠금/공조 명령이 `ACCEPTED` 되면 Home Assistant 상태를 목표 상태로 즉시 반영한 뒤 최대 약 24초 동안 실제 상태 수렴을 확인합니다. 차량 상태 반영이 더 늦으면 잠시 기다린 뒤 `차량 상태 새로고침`을 눌러 확인하세요.

## 수동 설치

HACS를 사용하지 않는 경우 아래 경로에 통합 폴더를 복사합니다.

```bash
cd ~/.homeassistant
mkdir -p custom_components
cp -R /path/to/smartthings-vehicle-ha/custom_components/smartthings_vehicle custom_components/
```

복사 후 Home Assistant를 재시작하세요.

## 라이선스

MIT
