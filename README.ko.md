# herdr-agent-cli

각 에이전트 뒤에 있는 CLI를 Herdr 사이드바에 고유한 색으로 표시합니다.

[![Herdr](https://img.shields.io/badge/herdr-0.9.0%2B-0797ff?logo=terminal&logoColor=white)](https://herdr.dev)
[![Python](https://img.shields.io/badge/python-3.8%2B-3776ab?logo=python&logoColor=white)](https://www.python.org/)
[![Platforms](https://img.shields.io/badge/platforms-macOS%20%7C%20Linux-lightgrey)](#설치)

영문 문서: [README.md](README.md)

<img src="docs/screenshots/sidebar.png" width="500"
     alt="Herdr sidebar: claude, agy, omp and codex each in their own colour, next to the agent names chewy-tofu, blue-heron, blue-lynx and slate-quokka">

Herdr는 자기가 감지한 런타임을 알고 있습니다. `rows_by_agent`가 바로 그 값으로 매칭하니까요.
그런데 그 값을 꺼내 쓸 내장 토큰이 없습니다. `agent` 토큰이 그리는 것은 *표시 이름*이라,
사이드바는 `chewy-tofu`만 보여줄 뿐 그 뒤가 Claude Code인지 Codex인지 omp인지 알려 주지
않습니다. 그래서 이 플러그인이 런타임을 pane metadata로 Herdr에 되돌려 보고합니다. 런타임을
사이드바 행에 올리려면 이 방법밖에 없습니다.

이름 쪽은 [agent-auto-naming](https://github.com/azyu/herdr-agent-auto-naming)이 만듭니다.
따로 써도 되지만, 위 스크린샷은 둘을 함께 쓴 모습입니다.

## 설치

Herdr 0.9.0 이상과 `python3`(표준 라이브러리만 사용)가 필요하며 macOS와 Linux에서 동작합니다.

```sh
herdr plugin install azyu/herdr-agent-cli
```

`cli` 토큰은 그것을 그려 줄 사이드바 행이 없으면 아무것도 표시하지 않는데, 색까지 입히는 행은
스무 줄이 넘습니다. 그래서 `configure.py`가 `[[startup]]` 훅에서 그 행들을
`~/.config/herdr/config.toml`에 기록합니다. `[[build]]`를 쓰지 않는 이유는 build가 런타임 환경을
받지 못하는 데다, `herdr plugin link`는 build 훅을 통째로 건너뛰기 때문입니다. 바꿀 것이 없는
실행은 아무것도 쓰지 않고 reload도 하지 않으므로, 재시작이 느려지지 않습니다.

`# >>> azyu.agent-cli >>>` 마커 사이에만 기록하고, 백업을 남기며,
`herdr server reload-config`가 결과를 거부하면 원본을 되돌립니다. TOML은 같은 테이블을 두 번
허용하지 않으므로, 이미 `[ui.sidebar.agents]` 블록이 있으면 중복 테이블을 만드는 대신 그냥
거부합니다. 기존 블록을 지우고 다시 실행하거나, 키를 손으로 옮겨 넣으세요.

**설치할 때 Herdr가 이미 떠 있었다면 이걸 한 번 실행하세요.** startup 훅은 서버가 시작할 때
돌기 때문에, 실행 중인 서버에 설치하면 행이 기록되지 않고 사이드바도 그대로입니다. Herdr를
재시작하거나 다음을 실행해야 합니다:

```sh
herdr plugin action invoke azyu.agent-cli.configure     # .unconfigure로 되돌립니다
```

심볼릭 링크도 따라가서 쓰고, 실제로 기록한 경로를 출력합니다.

설치 시점에 이미 실행 중이던 에이전트는 한 번 쓸어 주기 전까지 비어 있습니다:

```sh
herdr plugin action invoke azyu.agent-cli.refresh
```

## 색

기본값은 `configure.py`의 `PALETTE` 목록입니다. 일부만 바꾸거나, 플러그인이 Herdr 설정을 아예
건드리지 않게 하려면 플러그인 전용 설정 디렉터리를 쓰세요. 플러그인을 업데이트해도 남아 있고,
Herdr 문서가 사용자 설정을 두라고 지정한 위치이기도 합니다:

```sh
$EDITOR "$(herdr plugin config-dir azyu.agent-cli)/config.toml"
```

```toml
colours = "off"        # Herdr 설정을 절대 건드리지 않음

[colors]
claude = "#ff8800"     # canonical agent id만, 모르는 id는 거부
```

## 건드리는 것

표시 전용 pane metadata 토큰 `cli` 하나뿐입니다. pane label과 에이전트 이름은 건드리지
않습니다. auto-naming이 이름을 다시 붙일 때 근거로 삼는 값이기 때문입니다. pane에서 에이전트가
빠지면 토큰을 즉시 비우고, 값이 바뀔 때만 기록합니다. metadata를 쓸 때마다 사이드바가 다시
그려지는데 status 이벤트는 꽤 자주 발생하기 때문입니다.

`pane.agent_detected`와 `pane.agent_status_changed`, 서버 시작 시, 그리고 **Refresh CLI
labels** 액션에서 실행됩니다.

## 저 설정에 대해

런타임을 별도 토큰으로 둔 이유는 색을 따로 입히기 위해서입니다. `pane report-metadata`가 제어
문자를 제거하므로 색을 값에 실어 보낼 수는 없습니다. 그리고 Herdr는 인접한 토큰을 `·`로 잇는데
이 구분자는 설정할 수 없습니다. 런타임과 이름이 한 줄에 붙어 나올 수 없는 이유입니다.

값에 따른 스타일은 Herdr의 토큰 `rules`에서 옵니다. 첫 번째로 일치하는 규칙이 우선하고, 그
규칙이 지정한 필드가 토큰의 값을 덮으며, 지정하지 않은 필드는 상속됩니다. 그래서 토큰에 준
`bold = true`는 `fg`만 지정한 규칙에서도 그대로 유지됩니다. 토큰 하나에 규칙은 **최대 16개**인데
canonical agent id는 22개라, 상한을 넘는 6개는 `rows_by_agent`로 갑니다. 이 항목은 해당
런타임의 레이아웃 전체를 대체하기 때문에 첫 번째 행이 그대로 반복되는데, `configure.py`가
`ROW1` 상수 하나에서 양쪽을 전개하므로 둘이 어긋날 일은 없습니다.

토큰 전경색은 `#RGB` / `#RRGGBB`만 받습니다. `fg = "cyan"`은 *did not match any variant of
untagged enum RawSidebarToken*으로 거부됩니다(Herdr 0.9.0에서 실측). 이름 있는 색은
`ui.accent`에서는 되지만 여기서는 안 됩니다.

`rows_by_agent` 키는 검증을 거칩니다. Herdr가 모르는 id는 *unknown canonical agent id*로
거부되고 ui 설정 전체가 이전 상태로 유지됩니다. 위 22개가 Herdr 0.9.0이 받아 주는 전부이고,
문서 페이지에 무엇이 적혀 있든 `aider`, `goose`, `windsurf`, `zed`, `mastra`,
`antigravity-cli`는 여기에 **포함되지 않습니다**. 색은 해당 CLI에 브랜드 색이 있으면
그것(`claude`, `gemini`, `grok`), 없으면 Catppuccin에서 골랐습니다.

## 색 구분만 필요하다면 이 플러그인은 필요 없습니다

Herdr는 이미 런타임을 알고 있습니다. CLI를 색으로만 구분해도 충분하다면, 내장 `agent` 토큰을
런타임별로 칠하고 플러그인은 건너뛰면 됩니다:

```toml
[ui.sidebar.agents.rows_by_agent]
claude = [["state_icon", "machine", "workspace", "tab"], [{ token = "agent", fg = "#d97757", bold = true }]]
codex  = [["state_icon", "machine", "workspace", "tab"], [{ token = "agent", fg = "#89dceb", bold = true }]]
```

다만 이렇게 하면 색이 붙는 쪽은 이름(`chewy-tofu`)이지 런타임이 아닙니다. `claude`라는 단어는
어디에도 나오지 않습니다. 이 플러그인은 그 단어를 화면에 올리기 위해서만 존재합니다.

## 문제 해결

**아무것도 안 보입니다.** `configure` 액션을 실행하세요. startup 훅은 Herdr 서버가 시작할 때만
돕니다. 거부된다면 이미 직접 만든 `[ui.sidebar.agents]` 블록이 있는 경우입니다. 어느 쪽이든
보고된 값 자체는 `herdr pane list`의 `tokens.cli`에서 확인할 수 있습니다.

**이름은 나오는데 런타임이 없습니다.** 플러그인 설치 전부터 돌던 pane입니다. `refresh` 액션을
실행하세요.

**모든 호출이 실패합니다.** `brew upgrade herdr` 후 예전 서버가 계속 떠 있으면 모든 명령이
`protocol_mismatch`를 반환합니다. 플러그인을 의심하기 전에 `herdr --version`과 서버 시작
시각을 비교하세요.

## 라이선스

MIT
