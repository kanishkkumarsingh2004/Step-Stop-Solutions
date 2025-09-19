
def convert_amount_to_words(amount):
    """Convert amount to words for receipt"""
    if amount == 0:
        return "Zero Rupees"
    units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
    teens = ["", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "Ten", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
    in_words = ""
    amount_int = int(amount)
    def num_to_words_hundreds(n):
        s = ""
        if n >= 100:
            s += units[n // 100] + " Hundred "
            n %= 100
        if n >= 20:
            s += tens[n // 10] + " "
            n %= 10
        elif 11 <= n <= 19:
            s += teens[n - 10] + " "
            return s
        if n >= 1:
            s += units[n] + " "
        return s
    lakhs = amount_int // 100000
    thousands = (amount_int % 100000) // 1000
    hundreds = amount_int % 1000
    if lakhs > 0:
        in_words += num_to_words_hundreds(lakhs) + "Lakh "
    if thousands > 0:
        in_words += num_to_words_hundreds(thousands) + "Thousand "
    if hundreds > 0:
        in_words += num_to_words_hundreds(hundreds)
    in_words = in_words.strip() + " Rupees Only"
    return in_words