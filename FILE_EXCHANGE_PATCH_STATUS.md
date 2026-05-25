# KRXA FILE EXCHANGE PATCH V15

## 추가된 기능

- `/files` 또는 `/file_exchange` 파일 교환 UI
- `/api/files` 파일 목록 조회
- `/api/files/upload` 파일 업로드
- `/api/files/download/<stored_name>` 파일 다운로드
- `/api/files/delete` 파일 삭제
- `storage/file_exchange/file_manifest.json` 파일 교환 manifest

## 의미

KRXA 통합관제 흐름에서 파일을 외부 채팅이 아니라 KRXA HTTPS 내부로 가져오는 단계다.
이후 LLM Bridge가 붙으면 업로드된 파일을 KRXAI 논의 context로 사용할 수 있다.

## Render 설정

Start Command는 유지:

```text
python app.py
```
