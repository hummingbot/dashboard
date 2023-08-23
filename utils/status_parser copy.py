class StatusParser:
    def __init__(self, input_str):
        self.lines = input_str.split("\n")
        # Check for the type of parser needed
        if "No active maker orders" in input_str:
            self.parser = self
        elif all(keyword in input_str for keyword in ['Exchange', 'Market', 'Side']):
            self.parser = SimplePMMScriptParser(self.lines)
        elif all(keyword in input_str for keyword in ['Level', 'Amount (Orig)']):
            self.parser = PMMStrategyParser(self.lines)
        else:
            raise ValueError("No matching string")

    def parse(self):
        return self.parser._parse()

    def _parse(self):
        if "No active maker orders" in self.lines:
            return "No active maker orders"
        raise NotImplementedError

class SimplePMMScriptParser:
    def __init__(self, lines):
        self.lines = lines

    def _parse(self):
        if "No active maker orders" in "\n".join(self.lines):
            return "No active maker orders"
        orders = []
        for i, line in enumerate(self.lines):
            if "Orders:" in line:
                start_idx = i + 1
                break
        lines = self.lines[start_idx + 1:]
        for line in lines:
            parts = line.split()
            if len(parts) < 5:
                continue
            order = {
                "id": parts[2] + parts[3] + parts[4] + (parts[5] if len(parts) > 5 else ""),
                "Exchange": parts[0],
                "Market": parts[1],
                "Side": parts[2],
                "Price": parts[3],
                "Amount": parts[4],
                "Age": " ".join(parts[5:]) if len(parts) > 5 else None
            }
            orders.append(order)
        return orders

class PMMStrategyParser:
    def __init__(self, lines):
        self.lines = lines

    def _parse(self):
        if "No active maker orders" in "\n".join(self.lines):
            return "No active maker orders"
        orders = []
        for i, line in enumerate(self.lines):
            if "Orders:" in line:
                start_idx = i + 1
                break
        lines = self.lines[start_idx + 1:]
        for line in lines:
            parts = line.split()
            if len(parts) < 6:
                continue
            order = {
                "id": parts[0] + parts[1] + parts[2] + parts[3] + parts[4] + (parts[6] if len(parts) > 6 else ""),
                "Level": parts[0],
                "Type": parts[1],
                "Price": parts[2],
                "Spread": parts[3],
                "Amount (Adj)": parts[4],
                "Amount (Orig)": parts[5],
                "Age": " ".join(parts[6:]) if len(parts) > 6 else None 
            }
            orders.append(order)
        return orders
