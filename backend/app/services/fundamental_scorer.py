"""Fundamental scorer service using GARP (Growth at Reasonable Price) methodology.

This service evaluates stocks based on fundamental metrics to identify
quality growth companies trading at reasonable valuations.

GARP Principles (Peter Lynch's approach):
1. P/E ratio should be less than or equal to growth rate (PEG < 1)
2. Consistent earnings and revenue growth
3. High ROE indicates quality management
4. Low debt-to-equity ensures financial stability
5. Reasonable P/B for asset-backed companies
"""

from dataclasses import dataclass
from typing import Optional

import structlog

from app.models.fundamental import FundamentalData

logger = structlog.get_logger()


@dataclass
class FundamentalScore:
    """Result from fundamental scoring analysis.

    Attributes:
        score: Overall score from 0-100
        grade: Letter grade (A+, A, B+, B, C, D)
        bullish_factors: Positive fundamental aspects
        bearish_factors: Negative fundamental aspects
        warnings: Risk factors or concerns
        detail_scores: Breakdown of individual component scores
    """
    score: float
    grade: str
    bullish_factors: list[str]
    bearish_factors: list[str]
    warnings: list[str]
    detail_scores: dict[str, float]


class FundamentalScorer:
    """Service for scoring stocks based on fundamental GARP analysis.

    Scoring methodology:
    - P/E Ratio (PEG): 0-25 points
    - Growth Quality: 0-30 points
    - ROE/ROCE: 0-25 points
    - Financial Health (Debt): 0-20 points
    Total: 0-100 points

    Grade mapping:
    - 90-100: A+ (Excellent GARP candidate)
    - 80-89: A (Very good GARP stock)
    - 70-79: B+ (Good fundamentals)
    - 60-69: B (Decent fundamentals)
    - 50-59: C (Average)
    - Below 50: D (Poor fundamentals)
    """

    def __init__(self):
        """Initialize the fundamental scorer."""
        self._pe_threshold = 25.0  # Reasonable P/E cutoff
        self._peg_threshold = 1.0  # PEG ratio threshold
        self._roe_threshold = 15.0  # Good ROE threshold
        self._debt_threshold = 1.0  # Acceptable debt/equity

    def score(self, data: FundamentalData) -> Optional[FundamentalScore]:
        """Score a stock based on fundamental metrics.

        Args:
            data: FundamentalData object with metrics

        Returns:
            FundamentalScore with detailed analysis or None if insufficient data
        """
        if not self._has_sufficient_data(data):
            logger.warning("Insufficient fundamental data for scoring", symbol=data.symbol)
            return None

        bullish_factors = []
        bearish_factors = []
        warnings = []
        detail_scores = {}

        # Calculate component scores
        pe_score = self._score_pe_ratio(
            data, bullish_factors, bearish_factors, warnings
        )
        growth_score = self._score_growth(
            data, bullish_factors, bearish_factors, warnings
        )
        roe_score = self._score_roe_roce(
            data, bullish_factors, bearish_factors, warnings
        )
        debt_score = self._score_debt_equity(
            data, bullish_factors, bearish_factors, warnings
        )

        detail_scores = {
            "pe_score": pe_score,
            "growth_score": growth_score,
            "roe_score": roe_score,
            "debt_score": debt_score,
        }

        total_score = pe_score + growth_score + roe_score + debt_score
        grade = self._get_grade(total_score)

        logger.info(
            "Fundamental scoring completed",
            symbol=data.symbol,
            score=total_score,
            grade=grade,
        )

        return FundamentalScore(
            score=round(total_score, 1),
            grade=grade,
            bullish_factors=bullish_factors,
            bearish_factors=bearish_factors,
            warnings=warnings,
            detail_scores=detail_scores,
        )

    def _has_sufficient_data(self, data: FundamentalData) -> bool:
        """Check if sufficient data is available for scoring.

        At minimum, need P/E or growth metrics for meaningful analysis.
        """
        return any([
            data.pe_ratio is not None,
            data.pb_ratio is not None,
            data.roe is not None,
            data.roce is not None,
            data.eps_growth is not None,
            data.revenue_growth is not None,
        ])

    def _score_pe_ratio(
        self,
        data: FundamentalData,
        bullish: list,
        bearish: list,
        warnings: list,
    ) -> float:
        """Score P/E ratio based on GARP principles.

        Score: 0-25 points

        GARP rule: P/E should be less than growth rate (PEG < 1)
        """
        score = 0.0

        pe = data.pe_ratio
        eps_growth = data.eps_growth

        if pe is None:
            return 0

        # Basic P/E assessment
        if pe < 15:
            score += 10
            bullish.append(f"Attractive P/E ratio ({pe:.1f})")
        elif pe < 25:
            score += 7
            bullish.append(f"Reasonable P/E ratio ({pe:.1f})")
        elif pe < 35:
            score += 4
        elif pe < 50:
            bearish.append(f"Elevated P/E ratio ({pe:.1f})")
        else:
            bearish.append(f"High P/E ratio ({pe:.1f}) - expensive")
            warnings.append("P/E ratio suggests overvaluation")

        # PEG ratio assessment (if growth data available)
        if eps_growth is not None and eps_growth > 0:
            peg = pe / eps_growth

            if peg < 0.8:
                score += 15
                bullish.append(f"Excellent PEG ratio ({peg:.2f}) - growth at bargain price")
            elif peg < 1.0:
                score += 12
                bullish.append(f"Good PEG ratio ({peg:.2f}) - reasonably priced growth")
            elif peg < 1.3:
                score += 6
                bullish.append(f"Acceptable PEG ratio ({peg:.2f})")
            elif peg > 2.0:
                bearish.append(f"High PEG ratio ({peg:.2f}) - paying too much for growth")
        elif eps_growth is None and pe < 20:
            # No growth data but low P/E is still positive
            score += 5

        return min(25, score)

    def _score_growth(
        self,
        data: FundamentalData,
        bullish: list,
        bearish: list,
        warnings: list,
    ) -> float:
        """Score growth metrics (EPS and Revenue growth).

        Score: 0-30 points

        Values consistent and healthy growth.
        """
        score = 0.0

        eps_growth = data.eps_growth
        revenue_growth = data.revenue_growth

        # EPS Growth scoring
        if eps_growth is not None:
            if eps_growth > 20:
                score += 15
                bullish.append(f"Excellent EPS growth ({eps_growth:.1f}%)")
            elif eps_growth > 15:
                score += 12
                bullish.append(f"Strong EPS growth ({eps_growth:.1f}%)")
            elif eps_growth > 10:
                score += 9
                bullish.append(f"Good EPS growth ({eps_growth:.1f}%)")
            elif eps_growth > 5:
                score += 5
            elif eps_growth > 0:
                score += 2
            elif eps_growth < -5:
                bearish.append(f"Declining EPS ({eps_growth:.1f}%)")
            elif eps_growth < 0:
                bearish.append(f"Negative EPS growth ({eps_growth:.1f}%)")
        else:
            score -= 2  # Missing data penalty

        # Revenue Growth scoring
        if revenue_growth is not None:
            if revenue_growth > 20:
                score += 15
                bullish.append(f"Excellent revenue growth ({revenue_growth:.1f}%)")
            elif revenue_growth > 15:
                score += 12
                bullish.append(f"Strong revenue growth ({revenue_growth:.1f}%)")
            elif revenue_growth > 10:
                score += 9
                bullish.append(f"Good revenue growth ({revenue_growth:.1f}%)")
            elif revenue_growth > 5:
                score += 5
            elif revenue_growth > 0:
                score += 2
            elif revenue_growth < -5:
                bearish.append(f"Declining revenue ({revenue_growth:.1f}%)")
            elif revenue_growth < 0:
                bearish.append(f"Negative revenue growth ({revenue_growth:.1f}%)")
        else:
            score -= 2  # Missing data penalty

        # Consistency bonus (if both positive and similar)
        if eps_growth and revenue_growth:
            if eps_growth > 0 and revenue_growth > 0:
                growth_diff = abs(eps_growth - revenue_growth)
                if growth_diff < 5:
                    score += 3
                    bullish.append("Consistent earnings and revenue growth")

        return max(0, min(30, score))

    def _score_roe_roce(
        self,
        data: FundamentalData,
        bullish: list,
        bearish: list,
        warnings: list,
    ) -> float:
        """Score return on capital metrics (ROE and ROCE).

        Score: 0-25 points

        High ROE/ROCE indicates efficient capital allocation and quality management.
        """
        score = 0.0

        roe = data.roe
        roce = data.roce

        # ROE scoring
        if roe is not None:
            if roe > 20:
                score += 15
                bullish.append(f"Exceptional ROE ({roe:.1f}%) - high quality earnings")
            elif roe > 15:
                score += 12
                bullish.append(f"Strong ROE ({roe:.1f}%) - efficient capital use")
            elif roe > 10:
                score += 8
                bullish.append(f"Good ROE ({roe:.1f}%)")
            elif roe > 5:
                score += 4
            elif roe < 0:
                bearish.append(f"Negative ROE ({roe:.1f}%)")
        else:
            score -= 3

        # ROCE scoring (complementary to ROE)
        if roce is not None:
            if roce > 20:
                score += 10
                bullish.append(f"Excellent ROCE ({roce:.1f}%)")
            elif roce > 15:
                score += 8
                bullish.append(f"Strong ROCE ({roce:.1f}%)")
            elif roce > 10:
                score += 5
            elif roce < 5:
                bearish.append(f"Low ROCE ({roce:.1f}%) - poor capital efficiency")
        else:
            score -= 2

        # ROE vs ROCE consistency check
        if roe and roce:
            if abs(roe - roce) > 15:
                # Large difference might indicate high leverage
                warnings.append(f"ROE ({roe:.1f}%) significantly higher than ROCE ({roce:.1f}%) - check leverage")

        return max(0, min(25, score))

    def _score_debt_equity(
        self,
        data: FundamentalData,
        bullish: list,
        bearish: list,
        warnings: list,
    ) -> float:
        """Score financial health based on debt-to-equity ratio.

        Score: 0-20 points

        Lower debt is generally better, especially for growth companies.
        """
        score = 0.0

        debt_to_equity = data.debt_to_equity

        if debt_to_equity is None:
            # Can't assess - neutral score
            return 5

        if debt_to_equity < 0.3:
            score += 20
            bullish.append(f"Very low debt-to-equity ({debt_to_equity:.2f}) - strong financial health")
        elif debt_to_equity < 0.5:
            score += 18
            bullish.append(f"Low debt-to-equity ({debt_to_equity:.2f})")
        elif debt_to_equity < 0.75:
            score += 15
            bullish.append(f"Conservative debt levels ({debt_to_equity:.2f})")
        elif debt_to_equity < 1.0:
            score += 10
            bullish.append(f"Manageable debt-to-equity ({debt_to_equity:.2f})")
        elif debt_to_equity < 1.5:
            score += 5
        elif debt_to_equity < 2.0:
            bearish.append(f"Moderate-high debt ({debt_to_equity:.2f})")
        elif debt_to_equity < 3.0:
            bearish.append(f"High debt-to-equity ({debt_to_equity:.2f})")
            warnings.append("Elevated debt levels - financial risk")
        else:
            bearish.append(f"Very high debt-to-equity ({debt_to_equity:.2f})")
            warnings.append("Excessive leverage - significant financial risk")

        return max(0, min(20, score))

    def _get_grade(self, score: float) -> str:
        """Convert numeric score to letter grade.

        Args:
            score: Numeric score from 0-100

        Returns:
            Letter grade (A+, A, B+, B, C, D)
        """
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B+"
        elif score >= 60:
            return "B"
        elif score >= 50:
            return "C"
        else:
            return "D"
