# Autopilot · 매일 아침 오늘의 장면

3D 세계를 한 번 만들어 두면, 매일 정해진 시간에 AI가 만든 스크립트가 그 안에서 영상을 새로 만들어요. 여기 있는 건 노을 빌라용 템플릿이에요. 등록(설치)은 하지 않은 상태로 들어 있으니, 내 컴퓨터에 맞게 경로를 채워 직접 등록하세요.

| 파일 | 역할 |
|---|---|
| `todays_scene.py` | 블렌더 안에서 실행. 날짜를 씨앗으로 시간대 · 날씨 · 카메라 구간을 고르고 세로 3초를 렌더 |
| `run_daily.sh` | Mac · Linux 실행 스크립트. GPU 잠금, 렌더, ffmpeg로 mp4 + 워터마크(선택) |
| `run_daily.ps1` | Windows PowerShell 버전 |
| `com.connectailab.todays-scene.plist.template` | macOS launchd: 매일 08:00 |
| `windows_task.txt` | Windows 작업 스케줄러: 매일 08:00 |

## 고르는 값

| 시간대 `--time` | 날씨 `--weather` | 카메라 `--shot` (원래 드론 경로의 구간) |
|---|---|---|
| `golden_hour`, `blue_hour`, `night`, `dawn` | `clear`, `mist`, `light_rain` | `drone_open` 1-72, `orbit` 73-144, `pool_reveal` 145-216, `arrival` 241-312 |

값을 안 주면 날짜로 골라요. 같은 날은 항상 같은 조합, 날마다 다른 조합. 고른 값과 해상도, 샘플 수는 `out/날짜/params.json`에 남아요.

## 순서

1. 모델 받기: `python tools/get_scene.py golden-hour-villa`
2. 손으로 한 번: `bash autopilot/run_daily.sh` (Windows: `powershell -ExecutionPolicy Bypass -File autopilot\run_daily.ps1`)
3. 렌더 없이 값만 확인: `blender -b scenes/blend/golden-hour-villa.blend -P autopilot/todays_scene.py -- --out out --dry-run`
4. 매일 등록
   - Mac: plist 템플릿의 `/PATH/TO/` 3곳을 채워 `~/Library/LaunchAgents/`에 복사 → `launchctl load ...`
   - Windows: `windows_task.txt`의 `schtasks` 한 줄
5. 끄기: `launchctl unload ...` 또는 `schtasks /Delete ...`

## 주의

- GPU 하나에 렌더는 하나. 스크립트는 잠금 파일(`blender_mcp_vibecoding.lock`, 시스템 임시 폴더)이 있으면 그날은 건너뛰어요.
- 컴퓨터가 08:00에 잠자고 있으면 돌지 않아요(macOS는 다음에 깨어날 때 실행).
- 비(`light_rain`)는 카메라 앞에 얇은 빗줄기 판을 띄우는 단순한 방식이에요. 더 좋게 만들고 싶으면 AI에게 맡기세요: "todays_scene.py의 비를 지오메트리 노드 빗줄기로 바꾸고, 물웅덩이 파문도 추가해줘."
- 렌더 시간은 GPU에 따라 크게 달라요. 처음엔 `--percent 50`으로 재 보세요.

---
English: `todays_scene.py` seeds a daily pick of time of day, weather and camera stretch, renders a 3 s vertical clip and writes `params.json`. `run_daily.sh` / `run_daily.ps1` add a GPU lock and an ffmpeg encode with an optional corner watermark. The launchd plist and the schtasks line are templates; nothing is installed for you.
