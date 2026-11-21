"""Static and deterministic contracts for the paid general recruitment options."""

from dataclasses import dataclass
from decimal import Decimal
import unittest

from test_upstream_task42 import event, section
from lib_1966_parser import scalar


PRICES = (
    (5_000, 15_000, 50_000, 500_000),
    (10_000, 25_000, 100_000, 1_000_000),
    (50_000, 100_000, 250_000, 2_000_000),
    (250_000, 1_000_000, 2_000_000, 5_000_000),
)
BANDS = (("0.99", "33.01"), ("33.99", "66.01"), ("66.99", "100.01"))


@dataclass
class Country:
    funds: int
    provinces: int
    seed: Decimal | None
    cooldown: int = 0
    generals: int = 0


def purchase(country, branches):
    """Evaluate the checked script shape, using one owned province per matched branch."""
    seed = country.seed if country.seed is not None else Decimal(0)
    for price, lower, upper, payments, days in branches:
        if (country.provinces and not country.cooldown and country.funds >= price
                and lower <= seed < upper):
            country.generals += 1
            for delta in payments:
                country.funds += delta
            country.cooldown = days


class MilitaryHirePaymentTests(unittest.TestCase):
    def test_options_only_hire_and_charge_an_eligible_owner(self):
        for index, prices in enumerate(PRICES):
            event_id = 10000101 + index
            options = [node for node in event("Military", event_id).children if node.key == "option"]
            self.assertEqual(len(options), 4)
            for letter, price, option in zip("ABCD", prices, options, strict=True):
                with self.subTest(event_id=event_id, option=letter, price=price):
                    self.assertEqual(scalar(option, "name"), f"EVTOPT{letter}{event_id}")
                    self.assertEqual([node.key for node in option.children], ["name"] + ["random_owned"] * 3)
                    branches = []
                    for branch, (lower, upper) in zip(option.children[1:], BANDS, strict=True):
                        self.assertEqual([node.key for node in branch.children], ["limit", "owner"])
                        limit = section(section(branch, "limit"), "owner")
                        balance, cooldown, minimum, maximum = limit.children
                        self.assertEqual((balance.key, balance.operator, balance.value), ("money", "=", str(price)))
                        self.assertEqual(cooldown.keyword, "not")
                        self.assertEqual(scalar(cooldown, "has_country_modifier"), "recently_hired_general")
                        minimum_limit = self.seed_limit(minimum)
                        self.assertEqual(maximum.keyword, "not")
                        maximum_limit = self.seed_limit(section(maximum, "check_variable"))
                        self.assertEqual((minimum_limit, maximum_limit), (Decimal(lower), Decimal(upper)))
                        owner = section(branch, "owner")
                        payments = (-2_000_000, -2_000_000, -1_000_000) if price == 5_000_000 else (-price,)
                        self.assertEqual([node.key for node in owner.children],
                                         ["define_general"] + ["treasury"] * len(payments) + ["add_country_modifier"])
                        self.assertEqual(scalar(owner.children[0], "name"), "John Cena")
                        actual_payments = tuple(int(node.value) for node in owner.children[1:-1])
                        self.assertEqual(actual_payments, payments)
                        modifier = owner.children[-1]
                        self.assertEqual(scalar(modifier, "name"), "recently_hired_general")
                        days = int(scalar(modifier, "duration"))
                        self.assertEqual(days, 30)
                        branches.append((int(balance.value), minimum_limit, maximum_limit, actual_payments, days))
                    self.check_cases(branches, price)

    def seed_limit(self, node):
        self.assertEqual(node.key, "check_variable")
        self.assertEqual(scalar(node, "which"), "random_seed")
        return Decimal(scalar(node, "value"))

    def check_cases(self, branches, price):
        for seed in map(Decimal, range(1, 101)):
            self.assertEqual(sum(low <= seed < high for _, low, high, _, _ in branches), 1)
        for funds in (price - 1, price, price + 1, 2 * price):
            for provinces in (0, 1, 5):
                for cooldown in (0, 1):
                    for value, in_band in (
                        (None, False), ("-1", False), ("0", False), ("0.98", False),
                        ("0.99", True), ("33", True), ("33.01", False), ("33.99", True),
                        ("34", True), ("66", True), ("66.01", False), ("66.99", True),
                        ("67", True), ("100", True), ("100.01", False), ("101", False),
                    ):
                        seed = Decimal(value) if value is not None else None
                        country = Country(funds, provinces, seed, cooldown)
                        expected = int(in_band and provinces > 0 and not cooldown and funds >= price)
                        # Two already-open windows both use the current country state.
                        purchase(country, branches)
                        purchase(country, branches)
                        self.assertEqual((country.generals, country.funds, country.cooldown),
                                         (expected, funds - expected * price, 30 if expected else cooldown))
