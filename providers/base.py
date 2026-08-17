from abc import abstractmethod, ABC

class FinanceProvider(ABC):
    @abstractmethod
    async def listar_transacoes(self, filtros):
        pass

    @abstractmethod
    async def criar_transacao(self, dados_transacao):
        pass