# Project Folder Watcher

Windows용 독립 데스크톱 앱입니다. DaVinci Resolve의 프로젝트 라이브러리 폴더(또는 그 안의 프로젝트 폴더가 직접 들어 있는 디렉터리)를 선택하면 새 하위 폴더를 감시합니다. 폴더가 연속된 검사에서 안정적으로 확인되면 폴더 이름을 프로젝트 제목으로 표시하고 목록에 기록합니다.

## 실행

Python 3.10 이상이 설치된 Windows에서 `folder_watcher.py`를 실행하세요.

```powershell
python folder_watcher.py
```

별도 패키지는 필요하지 않습니다. Python 기본 Tkinter UI와 1.5초 간격의 디렉터리 검사를 사용합니다. 감시 경로는 `%APPDATA%\ProjectFolderWatcher\settings.json`에 저장됩니다. 앱을 다시 시작하면 기존 하위 폴더를 목록에 불러오고 이후 새로 생기는 폴더만 알립니다.

## 사용

1. Resolve 프로젝트 폴더들이 직접 들어 있는 상위 폴더를 선택합니다.
2. 앱을 켜 둡니다.
3. 새 하위 폴더가 안정적으로 생성되면 폴더 이름이 제목 배너에 표시되고 목록 맨 위에 추가됩니다.

폴더 감시 방식이므로 디스크 기반 라이브러리에 적합합니다. PostgreSQL 네트워크 라이브러리는 폴더 감시만으로 감지할 수 없습니다.
