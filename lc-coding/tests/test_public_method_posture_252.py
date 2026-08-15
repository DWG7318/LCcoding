from pathlib import Path
import re


root = Path(__file__).resolve().parents[2]


def require(relative, *markers):
    text = (root / relative).read_text(encoding="utf-8")
    for marker in markers:
        assert marker.casefold() in text.casefold(), f"{relative}: {marker}"


require(
    "README.md",
    "personal ability, knowledge structure, and recurring project practice",
    "study and adapt LCCoding",
    "discussion and contributions",
    "canonical mainline",
)
require(
    "README.zh-CN.md",
    "个人能力、知识结构和经常处理的项目实践",
    "借鉴并按自己的能力、知识范围和项目条件微调",
    "讨论和贡献",
    "规范主线",
)
require(
    "lc-coding/SKILL.md",
    "Agent-native integration",
    "references/agent-native-integration.md",
)
require(
    "README.md",
    "Agent-native integration",
    "lc-coding/references/agent-native-integration.md",
)
require(
    "README.zh-CN.md",
    "Agent-native 集成",
    "lc-coding/references/agent-native-integration.md",
)


def navigation_targets(relative):
    text = (root / relative).read_text(encoding="utf-8")
    targets = set()
    for target in re.findall(r"\[[^]]+\]\(([^)#]+)(?:#[^)]+)?\)", text):
        if target.startswith(("http://", "https://")):
            continue
        resolved = ((root / relative).parent / target).resolve()
        assert resolved.exists(), f"{relative}: missing navigation target {target}"
        normalized = resolved.relative_to(root.resolve()).as_posix()
        if normalized not in {"README.md", "README.zh-CN.md"}:
            targets.add(normalized)
    return targets


english_navigation = navigation_targets("README.md")
chinese_navigation = navigation_targets("README.zh-CN.md")
assert english_navigation == chinese_navigation, (
    "English/Chinese canonical and focused navigation must be equivalent: "
    f"EN-only={sorted(english_navigation - chinese_navigation)}; "
    f"ZH-only={sorted(chinese_navigation - english_navigation)}"
)
assert {
    "SPEC.md",
    "CONSTITUTION.md",
    "lc-coding/SKILL.md",
    "lc-coding/references/project-initialization.md",
    "lc-coding/references/feature-slice-and-integration.md",
    "lc-coding/references/loop-method-selection.md",
    "lc-coding/references/loop-acceptance-boundary.md",
    "lc-coding/references/vulnerability-closure.md",
    "lc-coding/references/delivery-governance.md",
    "lc-coding/references/built-in-bi.md",
    "lc-coding/references/agent-native-integration.md",
}.issubset(english_navigation)

print("PASS: public method posture preserves adaptable use and canonical ownership")
