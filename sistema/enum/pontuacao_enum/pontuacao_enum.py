from enum import Enum

class TipoAcaoEnum(Enum):
    CADASTRO = "cadastro"
    EDICAO = "edicao"

    @property
    def pontos(self):
        return {
            TipoAcaoEnum.CADASTRO: 1.0,
            TipoAcaoEnum.EDICAO: 0.5,
        }[self]
