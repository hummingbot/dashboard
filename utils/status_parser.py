class StatusParser:
    def __init__(self, input_str):
        self.lines = input_str.split("\n")
        
        # Check for the type of parser needed
        if "No active maker orders" in input_str:
            self.parser = self
        elif all(keyword in input_str for keyword in ['Exchange', 'Market', 'Side']):
            self.parser = OrderParser(self.lines, ['Exchange', 'Market', 'Side', 'Price', 'Amount', 'Age'])
        elif all(keyword in input_str for keyword in ['Level', 'Amount (Orig)']):
            self.parser = OrderParser(self.lines, ['Level', 'Type', 'Price', 'Spread', 'Amount (Adj)', 'Amount (Orig)', 'Age'])
        else:
            raise ValueError("No matching string")

    def parse(self):
        return self.parser._parse()

    def _parse(self):
        if "No active maker orders" in self.lines:
            return "No active maker orders"
        raise NotImplementedError

class OrderParser:
    def __init__(self, lines, columns):
        self.lines = lines
        self.columns = columns

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
            if len(parts) < len(self.columns):
                continue
            
            # Create the order dictionary based on provided columns
            order = {}
            for idx, col in enumerate(self.columns):
                order[col] = parts[idx]
                
            # Special handling for 'id' column (concatenating several parts)
            if 'id' not in order:
                order['id'] = ''.join(parts[:len(self.columns)-1])
                
            orders.append(order)
        
        return orders
