# SPDX-FileCopyrightText: Copyright (c) 2023-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pytest
from fastapi.testclient import TestClient

from nemoguardrails.actions_server import actions_server

client = TestClient(actions_server.app)


@pytest.mark.skip(reason="Should only be run locally as it fetches data from wikipedia.")
@pytest.mark.parametrize(
    "action_name, action_parameters, result_field, status",
    [
        (
            "action-test",
            {"content": "Hello", "parameter": "parameters"},
            [],
            "failed",
        ),
        ("Wikipedia", {"query": "president of US?"}, ["text"], "success"),
    ],
)
def test_run(action_name, action_parameters, result_field, status):
    response = client.post(
        "/v1/actions/run",
        json={
            "action_name": action_name,
            "action_parameters": action_parameters,
        },
    )

    assert response.status_code == 200
    res = response.json()
    assert list(res["result"].keys()) == result_field
    assert res["status"] == status


def test_get_actions():
    response = client.get("/v1/actions/list")

    # Check that we have at least one config
    result = response.json()
    assert len(result) >= 1


@pytest.mark.parametrize(
    "action_result",
    [True, False, 0.75, ["a", "b"], {"text": "x", "score": 1}, "ok", None],
    ids=["true", "false", "float", "list", "dict", "str", "none"],
)
def test_run_returns_non_string_results(monkeypatch, action_result):
    """Actions can return any JSON value, not only strings.

    The Colang runtimes read ``result`` back as-is, and rail actions
    commonly return booleans or dicts, so the endpoint must not reject them.
    """

    async def fake_execute_action(action_name, params):
        return action_result, "success"

    monkeypatch.setattr(actions_server.app.action_dispatcher, "execute_action", fake_execute_action)

    response = client.post(
        "/v1/actions/run",
        json={"action_name": "any_action", "action_parameters": {}},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "success", "result": action_result}
