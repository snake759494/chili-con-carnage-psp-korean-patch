# 빌드 방법

필요한 것: Python 3, Pillow, NumPy, OpenCV(`opencv-python`), pycdlib. 에뮬레이터 확인용으로 websocket-client.

1. 원본 ISO를 풉니다.
   `python tools/extract_iso.py "Chili Con Carnage (USA).iso" work/iso`
2. 번역 대본을 `translation/ko/<블록 이름>.txt` 에 둡니다. 한 줄에 `슬롯번호<TAB>문장` 형식입니다. (대본은 저장소에 포함하지 않습니다.)
3. 저장소 루트에 `NanumSquareNeo-cBd.ttf`, `NanumSquareNeo-bRg.ttf` 를 둡니다.
4. 빌드합니다.
   `python tools/build.py "Chili Con Carnage (Korean).iso"`
5. `python tools/check.py` 로 번역문 검사를 하고, xdelta를 만듭니다.
   `xdelta3 -e -0 -s "Chili Con Carnage (USA).iso" "Chili Con Carnage (Korean).iso" ChiliConCarnage_KR.xdelta`

`tools/emu.py`·`tools/ppsspp_rpc.py` 는 PPSSPP 디버거(WebSocket)로 에뮬레이터를 조작하고 화면을 캡처하는 도구입니다.
