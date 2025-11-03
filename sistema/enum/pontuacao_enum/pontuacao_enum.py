from enum import Enum

class TipoAcaoEnum(Enum):
    CADASTRO = "cadastro"
    EDICAO = "edicao"

    @property #método da classe em um atributo de leitura 
    def pontos(self):
        return {
            TipoAcaoEnum.CADASTRO: 1.0,
            TipoAcaoEnum.EDICAO: 0.5,
        }[self]
