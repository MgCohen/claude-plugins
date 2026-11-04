import unittest

from notion_context.snippet_range import snippet_range
from notion_context.snippets import follow_range

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

    def test_crlf(self):
        self.assertEqual(snippet_range(CS.replace("\n", "\r\n"), "Total"), (13, 17))

    def test_csharp_syntax(self):
        code = 'class A\n{\n    string s = """\n    } {\n    """;\n    [Route("x")] public void Get() { }\n    void M<T<int>>() { }\n}\n'
        self.assertEqual(snippet_range(code, "Get"), (6, 6))
        self.assertEqual(snippet_range(code, "M"), (7, 7))

    def test_typescript(self):
        self.assertEqual(snippet_range(TS, "Cart.total"), (6, 9))
        self.assertEqual(snippet_range(TS, "items"), (4, 4))
        self.assertEqual(snippet_range(TS, "format"), (12, 14))

    def test_errors(self):
        self.assertRaisesRegex(ValueError, 'No declaration named "Missing"', snippet_range, CS, "Missing")
        self.assertRaisesRegex(ValueError, "Only 3 declaration", snippet_range, CS, "Total", overload=4)
        self.assertRaisesRegex(ValueError, "Bad method name", snippet_range, CS, "Total-B3")
        self.assertRaisesRegex(ValueError, "Overload must be", snippet_range, CS, "Total", overload=-1)
        self.assertRaisesRegex(ValueError, "Overload must be", snippet_range, CS, "Total", before=-5)


class FollowRangeTests(unittest.TestCase):
    def test_hunks(self):
        self.assertEqual(follow_range("@@ -2,0 +3,2 @@", 10, 20), (12, 22, False))
        self.assertEqual(follow_range("@@ -12 +12,3 @@", 10, 20), (10, 22, True))
        self.assertEqual(follow_range("@@ -18,8 +17,0 @@", 10, 20), (10, 17, True))
        self.assertEqual(follow_range("@@ -5,3 +4,0 @@", 6, 20), (5, 17, True))
        self.assertEqual(follow_range("@@ -20,0 +21,3 @@", 10, 20), (10, 20, False))
        self.assertEqual(follow_range("@@ -9,0 +10,2 @@\n@@ -30,1 +32,0 @@", 10, 20), (12, 22, False))


if __name__ == "__main__":
    unittest.main()
