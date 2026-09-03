"""Tests for config models: from_dict and merge."""

from typing import Any

import pytest

from vcr_tui.config.models import Channel, Config, ExtractionRule


class TestFromDict:
    def test_empty_dict_gives_defaults(self) -> None:
        config = Config.from_dict({})
        assert config.root is False
        assert config.channels == ()
        assert config.default_channel is None

    @pytest.mark.parametrize(
        ('data', 'expected'),
        [
            ({'root': True}, Config(root=True)),
            ({'default_channel': 'x'}, Config(default_channel='x')),
            (
                {
                    'channels': {
                        'vcr': {
                            'glob_patterns': ['**/c.yaml'],
                            'extraction_rules': [
                                {
                                    'path': '.a',
                                    'formatter': 'json',
                                    'label': 'A',
                                    'metadata_keys': ['k'],
                                }
                            ],
                        }
                    }
                },
                Config(
                    channels=(
                        Channel(
                            name='vcr',
                            glob_patterns=('**/c.yaml',),
                            extraction_rules=(
                                ExtractionRule(
                                    path='.a',
                                    formatter='json',
                                    label='A',
                                    metadata_keys=('k',),
                                ),
                            ),
                        ),
                    )
                ),
            ),
        ],
    )
    def test_from_dict(self, data: dict[str, Any], expected: Config) -> None:
        assert Config.from_dict(data) == expected

    def test_channel_defaults(self) -> None:
        config = Config.from_dict({'channels': {'c': {}}})
        channel = config.channels[0]
        assert channel.name == 'c'
        assert channel.glob_patterns == ()
        assert channel.extraction_rules == ()
        assert channel.enabled is True

    def test_channel_disabled(self) -> None:
        config = Config.from_dict({'channels': {'c': {'enabled': False}}})
        assert config.channels[0].enabled is False

    def test_rule_defaults(self) -> None:
        config = Config.from_dict(
            {'channels': {'c': {'extraction_rules': [{'path': '.p', 'formatter': 'text'}]}}}
        )
        rule = config.channels[0].extraction_rules[0]
        assert rule.label is None
        assert rule.metadata_keys == ()

    def test_get_channel(self) -> None:
        config = Config.from_dict(
            {
                'default_channel': 'b',
                'channels': {'a': {}, 'b': {}},
            }
        )
        named = config.get_channel('a')
        assert named is not None
        assert named.name == 'a'
        default = config.get_channel()
        # default_channel wins
        assert default is not None
        assert default.name == 'b'
        assert config.get_channel('zzz') is None

    def test_get_channel_falls_back_to_first(self) -> None:
        config = Config.from_dict({'channels': {'a': {}, 'b': {}}})
        channel = config.get_channel()
        assert channel is not None
        assert channel.name == 'a'

    def test_get_channel_empty_config(self) -> None:
        assert Config().get_channel() is None


class TestMerge:
    def test_merge_adds_new_channels(self) -> None:
        base = Config.from_dict({'channels': {'a': {}}})
        other = Config.from_dict({'channels': {'b': {}}})
        merged = base.merge(other)
        assert {ch.name for ch in merged.channels} == {'a', 'b'}

    def test_merge_overrides_existing_channel(self) -> None:
        base = Config.from_dict(
            {'channels': {'a': {'glob_patterns': ['**/base.yaml'], 'enabled': False}}}
        )
        other = Config.from_dict({'channels': {'a': {'glob_patterns': ['**/other.yaml']}}})
        merged = base.merge(other)
        channel = next(ch for ch in merged.channels if ch.name == 'a')
        assert channel.glob_patterns == ('**/other.yaml',)
        assert channel.enabled is True

    @pytest.mark.parametrize(
        ('base', 'other', 'expected'),
        [
            (Config(), Config(root=True), Config(root=True)),
            (Config(root=True), Config(), Config(root=True)),  # root is sticky
            (Config(default_channel='a'), Config(default_channel='b'), Config(default_channel='b')),
            (Config(default_channel='a'), Config(), Config(default_channel='a')),
        ],
    )
    def test_merge_scalars(self, base: Config, other: Config, expected: Config) -> None:
        assert base.merge(other) == expected
