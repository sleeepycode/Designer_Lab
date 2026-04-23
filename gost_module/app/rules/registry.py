from app.rules.font_rules import FontNameRule, FontSizeRule
from app.rules.spacing_rules import (
    FirstLineIndentRule,
    LineSpacingRule,
    SpaceBeforeAfterRule,
    AlignmentRule,
)
from app.rules.margin_rules import MarginRule
from app.rules.title_page_rules import TitlePageExistsRule, TitlePageContentRule
from app.rules.heading_rules import HeadingPeriodRule


def get_rules():
    return [
        MarginRule(),
        TitlePageExistsRule(),
        TitlePageContentRule(),
        FontNameRule(),
        FontSizeRule(),
        FirstLineIndentRule(),
        LineSpacingRule(),
        SpaceBeforeAfterRule(),
        AlignmentRule(),
        HeadingPeriodRule(),
    ]
