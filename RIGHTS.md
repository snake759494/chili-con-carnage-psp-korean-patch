# 권리 및 외부 자료

이 저장소는 비공식 한국어 패치의 제작 도구·기술 문서 공개용입니다. 원작 게임 「Chili Con Carnage」(PSP, Deadline Games 개발 / Eidos Interactive 발매)과 그 텍스트·이미지·음성·실행 코드의 권리는 원 권리자에게 있습니다. 원본 게임, 패치 적용 게임, 게임에서 추출한 데이터·이미지·음성·글꼴은 배포하지 않으며, 릴리즈에는 원본 디스크 이미지가 있어야만 쓸 수 있는 차분 파일(xdelta)만 첨부합니다. `docs/images` 의 스크린샷은 패치 결과를 보여 주기 위한 화면 캡처입니다.

영어 원문과 번역 대본(`translation/`)은 저장소에 넣지 않았습니다. 부팅 화면 한글 문구는 `tools/bootimg.py` 에 들어 있습니다.

저장소 공개 자체가 모든 파일에 동일한 오픈소스 라이선스를 부여한다는 뜻은 아닙니다. 자체 제작 코드에 대한 별도 포괄 라이선스는 현재 지정하지 않았습니다. `tools/ppsspp_rpc.py`, `tools/emu.py`, `tools/swz.py` 등 일부 도구는 같은 제작자의 다른 한글패치 저장소에서 가져온 것입니다.

글꼴 파일은 배포하지 않습니다(`docs/FONT_CREDITS.md`). xdelta, PPSSPP, Python 라이브러리(Pillow, NumPy, OpenCV, pycdlib, websocket-client 등) 등 외부 도구는 각 프로젝트의 라이선스를 따르며 바이너리를 재배포하지 않습니다.
