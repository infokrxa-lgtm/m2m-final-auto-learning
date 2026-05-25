# KRXA REALTIME AUTONOMOUS WEBSOCKET BUILD V31.7

## 핵심
- 실시간 이벤트 버스
- /api/realtime/status
- /api/realtime/events SSE fallback
- /api/autonomous/status
- /api/autonomous/tick
- /desktop, /hts, /HTS 모두 지원
- HTS 화면 상단 AUTO TICK 버튼
- 5초 realtime status 표시

## 안전 원칙
무제한 background loop는 기본 비활성.
사용자/관리자 trigger 기반 safe tick으로 실행.
Render Free 환경에서는 WebSocket보다 SSE/polling fallback을 기본 사용.
