from abc import abstractmethod, ABC

class FinanceProvider(ABC):
    @abstractmethod
    async def listar_transacoes(self, filtros):
        pass

    @abstractmethod
    async def criar_transacao(self, dados_transacao):
        pass

    @abstractmethod
    async def listar_categorias(self, tipo_transacao):
        pass

    @abstractmethod
    async def listar_contas(self):
        pass

    @abstractmethod
    async def listar_cartoes(self):
        pass