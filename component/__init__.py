"""빌드 도구 없이 동작하는 양방향 Streamlit 게임 컴포넌트입니다."""
from pathlib import Path
import streamlit.components.v1 as components
_game=components.declare_component('future_village',path=str(Path(__file__).parent/'frontend'))
def game(data,key='future_village'):
    return _game(data=data,key=key,default=None)
