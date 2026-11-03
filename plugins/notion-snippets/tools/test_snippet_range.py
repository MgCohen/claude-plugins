import unittest

from snippet_range import snippet_range

CS = """public class Billing
{
    // Total(order) in a comment
    private const string Note = "Total(x) { not code }";
    private const string Folder = @"C:\\temp\\";

    public void Run(Order o)
    {
        var t = Total(o);
        Log($"total is {t}");
    }

    public decimal Total(Order order)
    {
        var brace = '{';
        return order.Sum;
    }

    public decimal Total(Order order, decimal tax) =>
        Total(order) * (1 + tax);

    public int Count => 0;

    public class Nested
    {
        public int Total() { return 0; }
    }
}
"""

TS = """total(order);

export class Cart {
  private items: Order[] = [];

  total(tax: number): number {
    const label = `total { ${tax} }`;
    return tax;
  }
}

export const format = (value: number) => {
  return value.toFixed(2);
};
"""


class SnippetRangeTests(unittest.TestCase):
    def test_line_range(self):
        self.assertEqual(snippet_range(CS, start=7, end=11), (7, 11))
        self.assertEqual(snippet_range(CS, start=25, end=99), (25, 28))
        self.assertEqual(snippet_range(CS), (1, 28))
        self.assertRaisesRegex(ValueError, "outside the file", snippet_range, CS, start=40)

    def test_method_skips_calls_comments_and_strings(self):
        self.assertEqual(snippet_range(CS, "Total"), (13, 17))
        self.assertEqual(snippet_range(CS, "Run"), (7, 11))
        self.assertEqual(snippet_range(CS, "Count"), (22, 22))

    def test_overload_and_nested(self):
        self.assertEqual(snippet_range(CS, "Total", overload=2), (19, 20))
        self.assertEqual(snippet_range(CS, "Nested.Total"), (26, 26))
        self.assertEqual(snippet_range(CS, "Billing.Nested"), (24, 27))

    def test_padding(self):
        self.assertEqual(snippet_range(CS, "Total", before=1, after=1), (12, 18))
        self.assertEqual(snippet_range(CS, "Billing", before=5, after=5), (1, 28))

    def test_follows_moved_code(self):
        self.assertEqual(snippet_range("// a\n// b\n" + CS, "Total"), (15, 19))
        self.assertEqual(snippet_range(CS.replace("\n", "\r\n"), "Total"), (13, 17))

    def test_typescript(self):
        self.assertEqual(snippet_range(TS, "Cart.total"), (6, 9))
        self.assertEqual(snippet_range(TS, "items"), (4, 4))
        self.assertEqual(snippet_range(TS, "format"), (12, 14))

    def test_errors(self):
        self.assertRaisesRegex(ValueError, 'No declaration named "Missing"', snippet_range, CS, "Missing")
        self.assertRaisesRegex(ValueError, "Only 3 declaration", snippet_range, CS, "Total", overload=4)
        self.assertRaisesRegex(ValueError, "Bad method name", snippet_range, CS, "Total-B3")


if __name__ == "__main__":
    unittest.main()
