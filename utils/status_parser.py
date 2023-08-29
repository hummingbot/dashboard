class StatusParser:
    def __init__(self, input_str, type='orders'):
        self.lines = input_str.split("\n")
        
        if type == 'orders':
            if "No active maker orders" in input_str:
                self.parser = self
            elif all(keyword in input_str for keyword in ['Orders:','Exchange', 'Market', 'Side', 'Price', 'Amount', 'Age']):
                self.parser = OrdersParser(self.lines, ['Exchange', 'Market', 'Side', 'Price', 'Amount', 'Age'])
            elif all(keyword in input_str for keyword in ['Orders:','Level', 'Amount (Orig)', 'Amount (Adj)']):
                self.parser = OrdersParser(self.lines, ['Level', 'Type', 'Price', 'Spread', 'Amount (Orig)', 'Amount (Adj)', 'Age'])
            else:
                raise ValueError("No matching string for type 'order'")
        elif type == 'balances':
            self.parser = BalancesParser(self.lines)
            # if all(keyword in input_str for keyword in ['Balances:']):
        else:
            raise ValueError(f"Unsupported type: {type}")

    def parse(self):
        return self.parser._parse()

    def _parse(self):
        if "No active maker orders" in self.lines:
            return "No active maker orders"
        raise NotImplementedError

class OrdersParser:
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

            # Ignore warning lines
            # if line.startswith("***"):
            #     break

            # Break when there's a blank line
            if not line.strip():
                break

            parts = line.split()
            if len(parts) < len(self.columns):
                continue
            
            # Create the orders dictionary based on provided columns
            order = {}
            for idx, col in enumerate(self.columns):
                order[col] = parts[idx]
                
            # Special handling for 'id' column (concatenating several parts)
            if 'id' not in order:
                order['id'] = ''.join(parts[:len(self.columns)-1])
                
            orders.append(order)
        
        return orders

class BalancesParser:
    def __init__(self, lines):
        self.lines = lines
        self.columns = ['Exchange', 'Asset', 'Total Balance', 'Available Balance']

    def _parse(self):
        # Check if "Balances:" exists in the lines
        if not any("Balances:" in line for line in self.lines):
            return "No balances"

        balances = []
        for i, line in enumerate(self.lines):
            if "Balances:" in line:
                start_idx = i + 1
                break

        lines = self.lines[start_idx + 1:]
        for line in lines:

            # Break when there's a blank line
            if not line.strip():
                break

            parts = line.split()
            if len(parts) < len(self.columns):
                continue
            
            # Create the balances dictionary based on provided columns
            balance = {}
            for idx, col in enumerate(self.columns):
                balance[col] = parts[idx]
                
            # Special handling for 'id' column (concatenating several parts)
            if 'id' not in balance:
                balance['id'] = ''.join(parts[:len(self.columns)-1])
                
            balances.append(balance)
        
        return balances