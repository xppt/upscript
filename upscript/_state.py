import json
import os
from typing import List, TYPE_CHECKING, Dict

state_path = 'xpm.json'


if TYPE_CHECKING:
    from typing import TypedDict

    class StateClientPackage(TypedDict):
        name: str


    class StateEntryPoint(TypedDict):
        name: str
        callable: str
        package: str


    class State(TypedDict):
        version: int
        index_url: str
        client_packages: List[StateClientPackage]
        entry_points: List[StateEntryPoint]
        index_hashes: Dict[str, str]
else:
    State = dict


def read_state(venv_path: str) -> State:
    with open(os.path.join(venv_path, state_path), encoding='utf-8') as file:
        state = json.load(file)

    assert state['version'] == 1, 'unsupported state version '
    return state


def write_state(state: State, venv_path: str) -> None:
    with open(os.path.join(venv_path, state_path), 'w', encoding='utf-8') as file:
        return json.dump(state, file, indent='\t')
