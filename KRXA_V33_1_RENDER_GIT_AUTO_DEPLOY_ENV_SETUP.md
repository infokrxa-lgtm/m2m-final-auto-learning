# KRXA V33.1 Render + GitHub 자동 배포 설정

## Render Environment에 추가

필수:

```text
GITHUB_TOKEN = github_pat_...
GITHUB_REPO = infokrxa-lgtm/KRXA
GITHUB_BRANCH = main
```

## GitHub Token 권한

Fine-grained token 권장:

```text
Repository: infokrxa-lgtm/KRXA
Permissions:
- Contents: Read and write
- Metadata: Read
```

## 사용 흐름

```text
/dev/edit 접속
→ 좌측 프로그램 트리에서 파일 선택
→ 코드 수정
→ 완료/저장
→ Git 자동배포
→ GitHub main 반영
→ Render Auto Deploy 실행
```

## 주의

app.py 변경은 GitHub 반영 후 Render 재배포가 완료되어야 실제 서비스에 반영됩니다.
core JSON 변경은 저장만으로도 실행 중인 서버에서 즉시 반영될 수 있습니다.
