import os
from pathlib import Path

class SQLManager:
    def __init__(self, sql_dir: str = "src/sql"):
        self.sql_dir = sql_dir
    
    def read_sql_file(self, filename: str) -> str:
        """Lê um arquivo SQL e retorna seu conteúdo."""
        with open(f"{self.sql_dir}/{filename}", "r") as f:
            return f.read()
    
    def get_user_info_sql(self, id_client: str) -> str:
        """Retorna a consulta SQL para informações do usuário com o ID do cliente substituído."""
        sql = self.read_sql_file("user_info.sql")
        return sql.format(id_client=id_client)
    
    def get_pix_concentration_sql(self, id_client: str) -> str:
        """Retorna a consulta SQL para concentração PIX com o ID do cliente substituído."""
        sql = self.read_sql_file("pix_concentration.sql")
        return sql.format(id_client=id_client)
    
    def get_card_transactions_sql(self, id_client: str) -> str:
        """Retorna a consulta SQL para transações de cartões com o ID do cliente substituído."""
        sql = self.read_sql_file("card_transactions.sql")
        return sql.format(id_client=id_client)
    
    def get_contact_info_sql(self, id_client: str) -> str:
        """Retorna a consulta SQL para informações de contato com o ID do cliente substituído."""
        sql = self.read_sql_file("contact_info.sql")
        return sql.format(id_client=id_client)
    
    def get_pep_transactions_sql(self, id_client: str) -> str:
        """Retorna a consulta SQL para transações PEP com o ID do cliente substituído."""
        sql = self.read_sql_file("pep_transactions.sql")
        return sql.format(id_client=id_client)
    
    def get_corporate_cards_sql(self, id_client: str) -> str:
        """Retorna a consulta SQL para cartões corporativos com o ID do cliente substituído."""
        sql = self.read_sql_file("corporate_cards.sql")
        return sql.format(id_client=id_client)

    def get_gafi_transactions_sql(self, id_client: str) -> str:
        sql = self.read_sql_file("gafi_transactions.sql")
        return sql.format(id_client=id_client)

    def get_international_transactions_sql(self, id_client: str) -> str:
        sql = self.read_sql_file("international_transactions.sql")
        return sql.format(id_client=id_client)

    def get_ted_transactions_sql(self, id_client: str) -> str:
        sql = self.read_sql_file("ted_transactions.sql")
        return sql.format(id_client=id_client)

    def get_issuing_transactions_sql(self, id_client: str) -> str:
        sql = self.read_sql_file("issuing_transactions.sql")
        return sql.format(id_client=id_client)

    def get_acquiring_transactions_sql(self, id_client: str) -> str:
        sql = self.read_sql_file("acquiring_transactions.sql")
        return sql.format(id_client=id_client) 