# KRXA HTTPS NODE PREPARE

상태: READY

원칙:

```text
내 컴퓨터 = 제작/검증 원본
build/KRXA_RELEASE.zip = 배포 산출물
외부 저장소 HTTPS URL = 호출 가능한 노드
core/storage_index.json = 위치 지도
```

사용 순서:

```bat
KRXA_PREPARE_HTTPS_RELEASE.bat
```

그 다음 `build/KRXA_RELEASE.zip`을 Google Drive / GitHub Release / 서버 / 클라우드에 업로드합니다.
HTTPS 주소가 생기면:

```bat
KRXA_REGISTER_HTTPS_NODE.bat https://YOUR_RELEASE_URL
```

확인:

```bat
python run_krxa.py status
```
