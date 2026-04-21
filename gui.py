"""Interface grafica em Tkinter para o projeto Did It Understand?."""

from __future__ import annotations

import json
import logging
import sys
import threading
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText


ROOT_DIR = Path(__file__).resolve().parent
PASTA_MAIS_OU_MENOS = ROOT_DIR / "mais_ou_menos"
PASTA_TOPZERA = ROOT_DIR / "topzera"
ARQUIVO_EXEMPLOS = PASTA_MAIS_OU_MENOS / "exemplos.json"

for pasta in (PASTA_MAIS_OU_MENOS, PASTA_TOPZERA):
    caminho = str(pasta)
    if caminho not in sys.path:
        sys.path.insert(0, caminho)

from avaliador import ConfiguracaoAvaliacao, avaliar_resposta
from avaliador_openai import avaliar_resposta_com_ia, carregar_configuracao


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
LOGGER = logging.getLogger("did_it_understand_gui")


CORES = {
    "fundo": "#F6F1E9",
    "cartao": "#FFFDF9",
    "campo": "#F0E8DB",
    "borda": "#D7C8B7",
    "texto": "#16202A",
    "texto_suave": "#5C6874",
    "navy": "#163A5C",
    "teal": "#1D8A78",
    "teal_claro": "#D8F2EC",
    "coral": "#E86E5C",
    "coral_claro": "#FCE1DD",
    "amarelo": "#D9A441",
    "amarelo_claro": "#F8EBC8",
    "cinza": "#E7DED1",
    "cinza_escuro": "#A89988",
    "branco": "#FFFFFF",
}

FONTES = {
    "titulo": ("Segoe UI Semibold", 26),
    "subtitulo": ("Segoe UI", 11),
    "secao": ("Segoe UI Semibold", 12),
    "corpo": ("Segoe UI", 10),
    "corpo_negrito": ("Segoe UI Semibold", 10),
    "botao": ("Segoe UI Semibold", 11),
    "placar": ("Segoe UI Semibold", 36),
    "placar_legenda": ("Segoe UI", 10),
}


@dataclass(slots=True)
class ResultadoTela:
    modo: str
    nota: float
    feedback: str
    resumo: str
    detalhes: str
    metricas: list[tuple[str, str]]


CampoEntrada = tk.Entry | ScrolledText


def carregar_exemplos() -> list[dict[str, str]]:
    """Le os cenarios prontos da versao classica para uso rapido na GUI."""
    if not ARQUIVO_EXEMPLOS.exists():
        return []

    try:
        with ARQUIVO_EXEMPLOS.open("r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except (OSError, json.JSONDecodeError):
        LOGGER.exception("Falha ao carregar exemplos da interface.")
        return []

    return [item for item in dados if isinstance(item, dict)]


def formatar_feedback(feedback: str) -> str:
    """Padroniza o feedback para uma forma mais amigavel na interface."""
    mapa = {
        "Nao entendeu": "Nao entendeu",
        "Não entendeu": "Nao entendeu",
        "Parcial": "Parcial",
        "Entendeu": "Entendeu",
    }
    return mapa.get(feedback, feedback.strip() or "Sem classificacao")


def cor_por_nota(nota: float) -> str:
    """Retorna a cor mais adequada para o resultado da avaliacao."""
    if nota >= 70:
        return CORES["teal"]
    return CORES["amarelo"] if nota >= 30 else CORES["coral"]


def montar_bloco_lista(titulo: str, itens: list[str], vazio: str) -> list[str]:
    """Converte uma lista textual em bloco legivel para o painel de detalhes."""
    linhas = [titulo]
    if itens:
        linhas.extend(f"- {item}" for item in itens)
    else:
        linhas.append(f"- {vazio}")
    return linhas


class DidItUnderstandGUI(tk.Tk):
    """Aplicacao desktop que unifica os dois avaliadores do repositrio."""

    def __init__(self) -> None:
        super().__init__()

        self.title("Did It Understand? | GUI")
        self.geometry("1360x840")
        self.minsize(1180, 760)
        self.configure(bg=CORES["fundo"])

        self.exemplos = carregar_exemplos()
        self.animacao_id: str | None = None
        self.nota_animada = 0.0
        self.operacao_em_execucao = False
        self.indice_exemplo_atual = -1

        self.modo_var = tk.StringVar(value="mais_ou_menos")
        self.remover_stopwords_var = tk.BooleanVar(value=True)
        self.aplicar_stemming_var = tk.BooleanVar(value=True)
        self.mostrar_detalhes_var = tk.BooleanVar(value=True)
        self.exemplo_info_var = tk.StringVar(
            value="Nenhum exemplo carregado. Se quiser, voce pode criar uma pergunta nova do zero."
        )
        self.status_var = tk.StringVar(
            value="Monte uma pergunta, defina o gabarito e escolha como deseja corrigir a resposta do usuario."
        )
        self.descricao_modo_var = tk.StringVar()
        self.resumo_var = tk.StringVar(value="O resultado vai aparecer aqui com nota, leitura tecnica e indicadores.")
        self.feedback_var = tk.StringVar(value="Pronto para corrigir")
        self.azure_status_var = tk.StringVar(value="Ainda nao validado.")

        self.metricas_titulos: list[tk.StringVar] = []
        self.metricas_valores: list[tk.StringVar] = []
        self.canvas_principal: tk.Canvas | None = None
        self.area_rolavel: tk.Frame | None = None
        self.area_rolavel_id: int | None = None

        self._configurar_estilos_ttk()
        self._criar_interface()
        self._atualizar_modo_visual()
        self._renderizar_resultado_inicial()

    def _configurar_estilos_ttk(self) -> None:
        """Aplica pequenos ajustes de estilo aos widgets ttk usados na GUI."""
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Custom.TCombobox",
            fieldbackground=CORES["branco"],
            background=CORES["branco"],
            foreground=CORES["texto"],
            bordercolor=CORES["borda"],
            lightcolor=CORES["borda"],
            darkcolor=CORES["borda"],
            arrowsize=14,
        )
        style.configure(
            "Brand.Horizontal.TProgressbar",
            troughcolor=CORES["cinza"],
            background=CORES["navy"],
            bordercolor=CORES["cinza"],
            lightcolor=CORES["navy"],
            darkcolor=CORES["navy"],
        )
        style.configure(
            "App.Vertical.TScrollbar",
            troughcolor=CORES["cinza"],
            background=CORES["navy"],
            arrowcolor=CORES["branco"],
            bordercolor=CORES["cinza"],
            lightcolor=CORES["navy"],
            darkcolor=CORES["navy"],
        )

    def _criar_interface(self) -> None:
        """Monta o layout principal da aplicacao."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        base = tk.Frame(self, bg=CORES["fundo"])
        base.grid(row=0, column=0, sticky="nsew")
        base.columnconfigure(0, weight=1)
        base.rowconfigure(0, weight=1)

        self.canvas_principal = tk.Canvas(
            base,
            bg=CORES["fundo"],
            bd=0,
            highlightthickness=0,
        )
        barra_rolagem = ttk.Scrollbar(
            base,
            orient="vertical",
            command=self.canvas_principal.yview,
            style="App.Vertical.TScrollbar",
        )
        self.canvas_principal.configure(yscrollcommand=barra_rolagem.set)
        self.canvas_principal.grid(row=0, column=0, sticky="nsew")
        barra_rolagem.grid(row=0, column=1, sticky="ns")

        container = tk.Frame(self.canvas_principal, bg=CORES["fundo"], padx=24, pady=24)
        container.columnconfigure(0, weight=7)
        container.columnconfigure(1, weight=6)
        container.rowconfigure(1, weight=1)
        self.area_rolavel = container
        self.area_rolavel_id = self.canvas_principal.create_window((0, 0), window=container, anchor="nw")

        container.bind("<Configure>", self._atualizar_scrollregion)
        self.canvas_principal.bind("<Configure>", self._ajustar_largura_area_rolavel)
        self.bind_all("<MouseWheel>", self._rolar_canvas_mousewheel)
        self.bind_all("<Button-4>", self._rolar_canvas_mousewheel)
        self.bind_all("<Button-5>", self._rolar_canvas_mousewheel)
        self.after_idle(self._atualizar_scrollregion)

        self._criar_header(container).grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 18))
        self._criar_painel_entrada(container).grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        self._criar_painel_resultado(container).grid(row=1, column=1, sticky="nsew", padx=(10, 0))

    def _atualizar_scrollregion(self, _event: tk.Event | None = None) -> None:
        """Atualiza a area total rolavel do canvas principal."""
        if self.canvas_principal is None:
            return
        self.canvas_principal.configure(scrollregion=self.canvas_principal.bbox("all"))

    def _ajustar_largura_area_rolavel(self, event: tk.Event) -> None:
        """Mantem o conteudo interno com a mesma largura visivel do canvas."""
        if self.canvas_principal is None or self.area_rolavel_id is None:
            return
        self.canvas_principal.itemconfigure(self.area_rolavel_id, width=event.width)

    def _rolar_canvas_mousewheel(self, event: tk.Event) -> str | None:
        """Permite rolagem vertical da janela com a roda do mouse."""
        if self.canvas_principal is None:
            return None

        widget = self.winfo_containing(event.x_root, event.y_root)
        if self._widget_tem_rolagem_propria(widget):
            return None

        direcao = 0
        if getattr(event, "delta", 0):
            passos = int(-event.delta / 120)
            direcao = passos if passos != 0 else (-1 if event.delta > 0 else 1)
        elif getattr(event, "num", None) == 4:
            direcao = -1
        elif getattr(event, "num", None) == 5:
            direcao = 1

        if direcao != 0:
            self.canvas_principal.yview_scroll(direcao, "units")
            return "break"
        return None

    def _widget_tem_rolagem_propria(self, widget: tk.Widget | None) -> bool:
        """Evita conflito entre a rolagem global e widgets que ja rolam sozinhos."""
        widget_atual = widget
        while widget_atual is not None:
            if isinstance(widget_atual, (tk.Text, tk.Listbox)):
                return True

            nome_classe = widget_atual.winfo_class()
            if nome_classe in {"Text", "Listbox", "TCombobox"}:
                return True

            nome_pai = widget_atual.winfo_parent()
            if not nome_pai:
                break
            try:
                widget_atual = widget_atual.nametowidget(nome_pai)
            except KeyError:
                break
        return False

    def _criar_header(self, parent: tk.Widget) -> tk.Frame:
        """Cria o bloco superior com contexto visual da aplicacao."""
        frame = tk.Frame(parent, bg=CORES["fundo"])
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=0)

        texto_frame = tk.Frame(frame, bg=CORES["fundo"])
        texto_frame.grid(row=0, column=0, sticky="w")

        tk.Label(
            texto_frame,
            text="Did It Understand?",
            bg=CORES["fundo"],
            fg=CORES["navy"],
            font=FONTES["titulo"],
        ).grid(row=0, column=0, sticky="w")

        tk.Label(
            texto_frame,
            text=(
                "Crie perguntas novas manualmente ou carregue um exemplo pronto quando quiser demonstrar o sistema mais rapido."
            ),
            bg=CORES["fundo"],
            fg=CORES["texto_suave"],
            font=FONTES["subtitulo"],
            wraplength=720,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        selo = tk.Label(
            texto_frame,
            text="Pergunta nova primeiro, exemplos prontos como atalho opcional",
            bg=CORES["teal_claro"],
            fg=CORES["navy"],
            font=FONTES["corpo_negrito"],
            padx=12,
            pady=6,
        )
        selo.grid(row=2, column=0, sticky="w", pady=(12, 0))

        arte = tk.Canvas(
            frame,
            width=220,
            height=88,
            bg=CORES["fundo"],
            bd=0,
            highlightthickness=0,
        )
        arte.grid(row=0, column=1, sticky="e")
        arte.create_oval(32, 14, 92, 74, fill=CORES["teal"], outline="")
        arte.create_oval(78, 4, 150, 76, fill=CORES["coral"], outline="")
        arte.create_oval(130, 18, 200, 80, fill=CORES["amarelo"], outline="")
        arte.create_text(112, 44, text="PLN", fill=CORES["branco"], font=("Segoe UI Semibold", 18))
        return frame

    def _criar_painel_entrada(self, parent: tk.Widget) -> tk.Frame:
        """Cria o painel com escolha de modo, entradas e acoes."""
        card = self._criar_cartao(parent)
        card.columnconfigure(0, weight=1)

        tk.Label(
            card,
            text="Criar nova avaliacao",
            bg=CORES["cartao"],
            fg=CORES["texto"],
            font=FONTES["secao"],
        ).grid(row=0, column=0, sticky="w")

        tk.Label(
            card,
            text=(
                "O uso principal desta tela e escrever uma pergunta nova, definir o gabarito e corrigir a resposta do usuario. "
                "Os exemplos servem apenas como atalho de demonstracao."
            ),
            bg=CORES["cartao"],
            fg=CORES["texto_suave"],
            font=FONTES["subtitulo"],
            wraplength=620,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(8, 0))

        frame_pergunta, self.texto_pergunta = self._criar_campo_entrada(
            card,
            titulo="Pergunta",
            dica="Escreva aqui uma nova pergunta. Nao precisa vir dos exemplos.",
        )
        frame_pergunta.grid(row=2, column=0, sticky="nsew", pady=(20, 0))

        frame_esperada, self.texto_esperada = self._criar_campo_entrada(
            card,
            titulo="Resposta esperada",
            dica="Defina o gabarito, ou seja, a resposta que representa o entendimento correto.",
        )
        frame_esperada.grid(row=3, column=0, sticky="nsew", pady=(18, 0))

        frame_usuario, self.texto_usuario = self._criar_campo_entrada(
            card,
            titulo="Resposta do usuario",
            dica="Cole aqui a resposta que sera corrigida com base na pergunta e no gabarito.",
        )
        frame_usuario.grid(row=4, column=0, sticky="nsew", pady=(18, 0))

        card_exemplos = self._criar_cartao_interno(card)
        card_exemplos.grid(row=5, column=0, sticky="ew", pady=(18, 0))
        card_exemplos.columnconfigure(0, weight=1)

        tk.Label(
            card_exemplos,
            text="Exemplos prontos, opcional",
            bg=CORES["cartao"],
            fg=CORES["texto"],
            font=FONTES["secao"],
        ).grid(row=0, column=0, sticky="w")

        tk.Label(
            card_exemplos,
            text=(
                "Se quiser demonstrar rapido, carregue um caso pronto. "
                "Se nao, ignore este bloco e crie sua pergunta normalmente."
            ),
            bg=CORES["cartao"],
            fg=CORES["texto_suave"],
            font=FONTES["subtitulo"],
            wraplength=560,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(8, 0))

        acoes_exemplo = tk.Frame(card_exemplos, bg=CORES["cartao"])
        acoes_exemplo.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        acoes_exemplo.columnconfigure(1, weight=1)

        self.botao_carregar = self._criar_botao_secundario(
            acoes_exemplo,
            texto="Carregar exemplo pronto",
            comando=self._carregar_exemplo,
        )
        self.botao_carregar.grid(row=0, column=0, sticky="w")

        tk.Label(
            acoes_exemplo,
            textvariable=self.exemplo_info_var,
            bg=CORES["cartao"],
            fg=CORES["texto_suave"],
            font=FONTES["subtitulo"],
            wraplength=380,
            justify="left",
        ).grid(row=0, column=1, sticky="w", padx=(14, 0))

        self.card_opcoes = self._criar_cartao_interno(card)
        self.card_opcoes.grid(row=6, column=0, sticky="ew", pady=(18, 0))
        self.card_opcoes.columnconfigure(0, weight=1)

        tk.Label(
            self.card_opcoes,
            text="Escolha como corrigir",
            bg=CORES["cartao"],
            fg=CORES["texto"],
            font=FONTES["secao"],
        ).grid(row=0, column=0, sticky="w")

        tk.Label(
            self.card_opcoes,
            text="Aqui voce decide se a correcao sera mais textual ou mais semantica.",
            bg=CORES["cartao"],
            fg=CORES["texto_suave"],
            font=FONTES["subtitulo"],
            wraplength=560,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(8, 0))

        modos = tk.Frame(self.card_opcoes, bg=CORES["cartao"])
        modos.grid(row=2, column=0, sticky="ew", pady=(14, 0))
        modos.columnconfigure(0, weight=1)
        modos.columnconfigure(1, weight=1)
        modos.rowconfigure(0, minsize=118)

        self.botao_mais_ou_menos = self._criar_botao_modo(
            modos,
            titulo="Mais ou Menos",
            descricao="Corrige por proximidade textual\nRapido, explicavel e barato",
            comando=lambda: self._selecionar_modo("mais_ou_menos"),
        )
        self.botao_mais_ou_menos.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        self.botao_topzera = self._criar_botao_modo(
            modos,
            titulo="Topzera",
            descricao="Corrige por significado\nMelhor para parafrases e nuance",
            comando=lambda: self._selecionar_modo("topzera"),
        )
        self.botao_topzera.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        tk.Label(
            self.card_opcoes,
            textvariable=self.descricao_modo_var,
            bg=CORES["cartao"],
            fg=CORES["texto_suave"],
            font=FONTES["subtitulo"],
            wraplength=560,
            justify="left",
        ).grid(row=3, column=0, sticky="w", pady=(12, 0))

        self.opcoes_local_frame = tk.Frame(self.card_opcoes, bg=CORES["cartao"])
        self.opcoes_local_frame.grid(row=4, column=0, sticky="ew", pady=(10, 0))

        self.check_stopwords = self._criar_check(
            self.opcoes_local_frame,
            texto="Remover stopwords para focar nos termos mais relevantes",
            variavel=self.remover_stopwords_var,
        )
        self.check_stopwords.grid(row=0, column=0, sticky="w")

        self.check_stemming = self._criar_check(
            self.opcoes_local_frame,
            texto="Aplicar stemming para aproximar flexoes e variacoes de palavras",
            variavel=self.aplicar_stemming_var,
        )
        self.check_stemming.grid(row=1, column=0, sticky="w", pady=(8, 0))

        self.check_detalhes = self._criar_check(
            self.opcoes_local_frame,
            texto="Mostrar tokens e radicais no painel tecnico",
            variavel=self.mostrar_detalhes_var,
        )
        self.check_detalhes.grid(row=2, column=0, sticky="w", pady=(8, 0))

        self.opcoes_ia_frame = tk.Frame(self.card_opcoes, bg=CORES["cartao"])
        self.opcoes_ia_frame.columnconfigure(0, weight=1)

        tk.Label(
            self.opcoes_ia_frame,
            text=(
                "Esse modo usa Azure OpenAI, entao depende de .env valido, internet "
                "e pode gerar custo por chamada."
            ),
            bg=CORES["cartao"],
            fg=CORES["texto_suave"],
            font=FONTES["subtitulo"],
            wraplength=560,
            justify="left",
        ).grid(row=0, column=0, sticky="w")

        self.botao_check_azure = self._criar_botao_secundario(
            self.opcoes_ia_frame,
            texto="Verificar credenciais do Azure",
            comando=self._verificar_configuracao_azure,
        )
        self.botao_check_azure.grid(row=1, column=0, sticky="w", pady=(12, 0))

        tk.Label(
            self.opcoes_ia_frame,
            textvariable=self.azure_status_var,
            bg=CORES["cartao"],
            fg=CORES["texto_suave"],
            font=FONTES["subtitulo"],
            wraplength=560,
            justify="left",
        ).grid(row=2, column=0, sticky="w", pady=(10, 0))

        acoes = tk.Frame(card, bg=CORES["cartao"])
        acoes.grid(row=7, column=0, sticky="ew", pady=(20, 0))
        acoes.columnconfigure(0, weight=0)
        acoes.columnconfigure(1, weight=0)
        acoes.columnconfigure(2, weight=1)

        self.botao_avaliar = self._criar_botao_principal(
            acoes,
            texto="Avaliar agora",
            comando=self._iniciar_avaliacao,
        )
        self.botao_avaliar.grid(row=0, column=0, sticky="w")

        self.botao_limpar = self._criar_botao_secundario(
            acoes,
            texto="Nova pergunta",
            comando=self._limpar_campos,
        )
        self.botao_limpar.grid(row=0, column=1, sticky="w", padx=(10, 0))

        self.progressbar = ttk.Progressbar(
            card,
            mode="indeterminate",
            style="Brand.Horizontal.TProgressbar",
        )
        self.progressbar.grid(row=8, column=0, sticky="ew", pady=(18, 0))

        tk.Label(
            card,
            textvariable=self.status_var,
            bg=CORES["cartao"],
            fg=CORES["texto_suave"],
            font=FONTES["subtitulo"],
            wraplength=620,
            justify="left",
        ).grid(row=9, column=0, sticky="w", pady=(10, 0))

        return card

    def _criar_painel_resultado(self, parent: tk.Widget) -> tk.Frame:
        """Cria o painel da direita com o resultado interpretado da avaliacao."""
        card = self._criar_cartao(parent)
        card.columnconfigure(0, weight=1)

        topo = tk.Frame(card, bg=CORES["cartao"])
        topo.grid(row=0, column=0, sticky="ew")
        topo.columnconfigure(0, weight=1)

        tk.Label(
            topo,
            text="Correcao da resposta",
            bg=CORES["cartao"],
            fg=CORES["texto"],
            font=FONTES["secao"],
        ).grid(row=0, column=0, sticky="w")

        tk.Label(
            topo,
            text="Depois de montar a pergunta e o gabarito, o painel abaixo mostra a nota e o por que da correcao.",
            bg=CORES["cartao"],
            fg=CORES["texto_suave"],
            font=FONTES["subtitulo"],
            wraplength=500,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(8, 0))

        destaque = tk.Frame(card, bg=CORES["campo"], padx=18, pady=18)
        destaque.grid(row=1, column=0, sticky="ew", pady=(18, 0))
        destaque.columnconfigure(0, weight=1)
        destaque.configure(highlightthickness=1, highlightbackground=CORES["borda"])

        self.canvas_medidor = tk.Canvas(
            destaque,
            width=460,
            height=170,
            bg=CORES["campo"],
            bd=0,
            highlightthickness=0,
        )
        self.canvas_medidor.grid(row=0, column=0, sticky="ew")

        self.label_feedback = tk.Label(
            destaque,
            textvariable=self.feedback_var,
            bg=CORES["navy"],
            fg=CORES["branco"],
            font=FONTES["corpo_negrito"],
            padx=14,
            pady=7,
        )
        self.label_feedback.grid(row=1, column=0, sticky="w", pady=(8, 0))

        tk.Label(
            destaque,
            textvariable=self.resumo_var,
            bg=CORES["campo"],
            fg=CORES["texto"],
            font=FONTES["subtitulo"],
            wraplength=500,
            justify="left",
        ).grid(row=2, column=0, sticky="w", pady=(12, 0))

        metricas_frame = tk.Frame(card, bg=CORES["cartao"])
        metricas_frame.grid(row=2, column=0, sticky="ew", pady=(20, 0))
        metricas_frame.columnconfigure(0, weight=1)
        metricas_frame.columnconfigure(1, weight=1)
        metricas_frame.columnconfigure(2, weight=1)
        metricas_frame.rowconfigure(0, weight=1)

        for indice in range(3):
            titulo_var = tk.StringVar(value="Indicador")
            valor_var = tk.StringVar(value="--")
            self.metricas_titulos.append(titulo_var)
            self.metricas_valores.append(valor_var)
            self._criar_card_metrica(metricas_frame, titulo_var, valor_var).grid(
                row=0,
                column=indice,
                sticky="nsew",
                padx=(0 if indice == 0 else 8, 0),
            )

        tk.Label(
            card,
            text="Leitura tecnica",
            bg=CORES["cartao"],
            fg=CORES["texto"],
            font=FONTES["secao"],
        ).grid(row=3, column=0, sticky="w", pady=(22, 0))

        self.texto_detalhes = ScrolledText(
            card,
            height=16,
            wrap="word",
            bg=CORES["campo"],
            fg=CORES["texto"],
            insertbackground=CORES["texto"],
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=CORES["borda"],
            font=FONTES["corpo"],
            padx=14,
            pady=14,
        )
        self.texto_detalhes.grid(row=4, column=0, sticky="nsew", pady=(10, 0))
        self.texto_detalhes.configure(state="disabled")

        card.rowconfigure(4, weight=1)
        return card

    def _criar_campo_entrada(self, parent: tk.Widget, titulo: str, dica: str) -> tuple[tk.Frame, tk.Entry]:
        """Cria um bloco reutilizavel com label, dica e um campo Entry."""
        frame = tk.Frame(parent, bg=CORES["cartao"])
        frame.columnconfigure(0, weight=1)

        tk.Label(
            frame,
            text=titulo,
            bg=CORES["cartao"],
            fg=CORES["texto"],
            font=FONTES["corpo_negrito"],
        ).grid(row=0, column=0, sticky="w")

        tk.Label(
            frame,
            text=dica,
            bg=CORES["cartao"],
            fg=CORES["texto_suave"],
            font=FONTES["subtitulo"],
            wraplength=620,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        casca = tk.Frame(
            frame,
            bg=CORES["branco"],
            highlightthickness=1,
            highlightbackground=CORES["borda"],
            highlightcolor=CORES["navy"],
            padx=12,
            pady=6,
        )
        casca.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        casca.columnconfigure(0, weight=1)

        campo = tk.Entry(
            casca,
            bg=CORES["branco"],
            fg=CORES["texto"],
            insertbackground=CORES["texto"],
            relief="flat",
            bd=0,
            highlightthickness=0,
            insertwidth=2,
            font=FONTES["corpo"],
        )
        campo.grid(row=0, column=0, sticky="ew", ipady=8)
        return frame, campo

    def _criar_cartao(self, parent: tk.Widget) -> tk.Frame:
        """Cria um cartao base do layout."""
        return tk.Frame(
            parent,
            bg=CORES["cartao"],
            highlightthickness=1,
            highlightbackground=CORES["borda"],
            padx=22,
            pady=22,
        )

    def _criar_cartao_interno(self, parent: tk.Widget) -> tk.Frame:
        """Cria um cartao menor usado em blocos internos da tela."""
        return tk.Frame(
            parent,
            bg=CORES["cartao"],
            highlightthickness=1,
            highlightbackground=CORES["cinza"],
            padx=18,
            pady=18,
        )

    def _criar_card_fluxo(
        self,
        parent: tk.Widget,
        numero: str,
        titulo: str,
        descricao: str,
        cor_fundo: str,
    ) -> tk.Frame:
        """Cria um card curto para explicar o passo atual do fluxo."""
        frame = tk.Frame(
            parent,
            bg=cor_fundo,
            highlightthickness=1,
            highlightbackground=CORES["borda"],
            padx=12,
            pady=12,
        )
        frame.columnconfigure(1, weight=1)

        badge = tk.Label(
            frame,
            text=numero,
            bg=CORES["navy"],
            fg=CORES["branco"],
            font=FONTES["corpo_negrito"],
            width=2,
            padx=4,
            pady=4,
        )
        badge.grid(row=0, column=0, sticky="nw")

        conteudo = tk.Frame(frame, bg=cor_fundo)
        conteudo.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        tk.Label(
            conteudo,
            text=titulo,
            bg=cor_fundo,
            fg=CORES["texto"],
            font=FONTES["corpo_negrito"],
            justify="left",
            wraplength=145,
        ).grid(row=0, column=0, sticky="w")

        tk.Label(
            conteudo,
            text=descricao,
            bg=cor_fundo,
            fg=CORES["texto_suave"],
            font=FONTES["subtitulo"],
            justify="left",
            wraplength=145,
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))
        return frame

    def _criar_card_metrica(
        self,
        parent: tk.Widget,
        titulo_var: tk.StringVar,
        valor_var: tk.StringVar,
    ) -> tk.Frame:
        """Cria um card pequeno para exibir metrica resumida."""
        frame = tk.Frame(
            parent,
            bg=CORES["branco"],
            highlightthickness=1,
            highlightbackground=CORES["borda"],
            padx=14,
            pady=14,
        )
        frame.columnconfigure(0, weight=1)
        frame.configure(height=118)
        frame.grid_propagate(False)

        tk.Label(
            frame,
            textvariable=titulo_var,
            bg=CORES["branco"],
            fg=CORES["texto_suave"],
            font=FONTES["subtitulo"],
            wraplength=150,
            justify="left",
        ).grid(row=0, column=0, sticky="w")

        tk.Label(
            frame,
            textvariable=valor_var,
            bg=CORES["branco"],
            fg=CORES["texto"],
            font=("Segoe UI Semibold", 16),
            wraplength=150,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(10, 0))
        return frame

    def _criar_botao_principal(self, parent: tk.Widget, texto: str, comando) -> tk.Button:
        """Cria o botao principal da tela."""
        return tk.Button(
            parent,
            text=texto,
            command=comando,
            bg=CORES["navy"],
            fg=CORES["branco"],
            activebackground=CORES["teal"],
            activeforeground=CORES["branco"],
            relief="flat",
            bd=0,
            highlightthickness=0,
            padx=18,
            pady=12,
            cursor="hand2",
            font=FONTES["botao"],
            disabledforeground=CORES["cinza"],
        )

    def _criar_botao_secundario(self, parent: tk.Widget, texto: str, comando) -> tk.Button:
        """Cria um botao secundario com visual mais neutro."""
        return tk.Button(
            parent,
            text=texto,
            command=comando,
            bg=CORES["branco"],
            fg=CORES["navy"],
            activebackground=CORES["teal_claro"],
            activeforeground=CORES["navy"],
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=CORES["borda"],
            padx=16,
            pady=10,
            cursor="hand2",
            font=FONTES["corpo_negrito"],
            disabledforeground=CORES["cinza_escuro"],
        )

    def _criar_botao_modo(self, parent: tk.Widget, titulo: str, descricao: str, comando) -> tk.Button:
        """Cria um botao grande usado para alternar entre os modos."""
        return tk.Button(
            parent,
            text=f"{titulo}\n{descricao}",
            command=comando,
            justify="left",
            anchor="w",
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=CORES["borda"],
            padx=18,
            pady=18,
            cursor="hand2",
            font=FONTES["corpo_negrito"],
            wraplength=250,
            height=4,
        )

    def _criar_check(self, parent: tk.Widget, texto: str, variavel: tk.BooleanVar) -> tk.Checkbutton:
        """Cria um checkbox com as cores do restante da interface."""
        return tk.Checkbutton(
            parent,
            text=texto,
            variable=variavel,
            bg=CORES["cartao"],
            fg=CORES["texto"],
            activebackground=CORES["cartao"],
            activeforeground=CORES["texto"],
            selectcolor=CORES["cartao"],
            font=FONTES["subtitulo"],
            anchor="w",
            justify="left",
            wraplength=560,
        )

    def _selecionar_modo(self, modo: str) -> None:
        """Altera o modo de avaliacao ativo na interface."""
        if self.operacao_em_execucao:
            return
        self.modo_var.set(modo)
        self._atualizar_modo_visual()

    def _atualizar_modo_visual(self) -> None:
        """Ajusta textos, botoes e opcoes conforme o modo atual."""
        modo = self.modo_var.get()
        if modo == "mais_ou_menos":
            self.descricao_modo_var.set(
                "Use este modo quando voce quer corrigir com criterios transparentes. "
                "Ele mostra a proximidade textual, as palavras-chave cobertas e o efeito do pre-processamento."
            )
            self.botao_avaliar.configure(text="Corrigir com Mais ou Menos", bg=CORES["navy"])
            self.botao_mais_ou_menos.configure(
                bg=CORES["teal"],
                fg=CORES["branco"],
                activebackground=CORES["teal"],
                activeforeground=CORES["branco"],
            )
            self.botao_topzera.configure(
                bg=CORES["campo"],
                fg=CORES["texto"],
                activebackground=CORES["coral_claro"],
                activeforeground=CORES["texto"],
            )
            self.opcoes_ia_frame.grid_forget()
            self.opcoes_local_frame.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        else:
            self.descricao_modo_var.set(
                "Use este modo quando a resposta do usuario pode vir com palavras bem diferentes do gabarito. "
                "Ele corrige pelo significado, mas depende de Azure OpenAI, conectividade e controle de custo."
            )
            self.botao_avaliar.configure(text="Corrigir com Topzera", bg=CORES["coral"])
            self.botao_topzera.configure(
                bg=CORES["coral"],
                fg=CORES["branco"],
                activebackground=CORES["coral"],
                activeforeground=CORES["branco"],
            )
            self.botao_mais_ou_menos.configure(
                bg=CORES["campo"],
                fg=CORES["texto"],
                activebackground=CORES["teal_claro"],
                activeforeground=CORES["texto"],
            )
            self.opcoes_local_frame.grid_forget()
            self.opcoes_ia_frame.grid(row=4, column=0, sticky="ew", pady=(10, 0))

    def _renderizar_resultado_inicial(self) -> None:
        """Exibe um estado neutro antes da primeira avaliacao."""
        self.feedback_var.set("Pronto para corrigir")
        self.resumo_var.set(
            "Crie uma pergunta nova ou carregue um exemplo pronto, depois escolha o tipo de correcao e acompanhe a nota aqui."
        )
        self._atualizar_metricas(
            [
                ("Etapa atual", "Criar pergunta"),
                ("Modo padrao", "Mais ou Menos"),
                ("Exemplos", "Opcionais"),
            ]
        )
        self._atualizar_detalhes(
            "\n".join(
                [
                    "A interface foi organizada para espelhar o fluxo real de uso do projeto.",
                    "",
                    "- O caminho principal e criar uma pergunta nova e registrar a resposta esperada.",
                    "- Depois cola a resposta do usuario para ser corrigida.",
                    "- Os exemplos prontos existem apenas para acelerar testes e demonstracoes.",
                    "- Por fim voce escolhe se quer uma correcao textual, no Mais ou Menos, ou uma correcao semantica, no Topzera.",
                    "",
                    "O objetivo da GUI e deixar a construcao da avaliacao e a leitura do resultado mais naturais.",
                ]
            )
        )
        self.label_feedback.configure(bg=CORES["navy"])
        self._animar_nota(0.0)

    def _carregar_exemplo(self) -> None:
        """Preenche a tela com um exemplo pronto do projeto."""
        if not self.exemplos:
            messagebox.showinfo("Exemplos", "Nenhum exemplo pronto foi encontrado no projeto.")
            return

        self.indice_exemplo_atual = (self.indice_exemplo_atual + 1) % len(self.exemplos)
        exemplo = self.exemplos[self.indice_exemplo_atual]

        self._definir_texto(self.texto_pergunta, exemplo.get("pergunta", ""))
        self._definir_texto(self.texto_esperada, exemplo.get("resposta_esperada", ""))
        self._definir_texto(self.texto_usuario, exemplo.get("resposta_usuario", ""))
        self.exemplo_info_var.set(
            f"Ultimo exemplo carregado: {exemplo.get('nome', 'Exemplo sem nome')}. Clique de novo para trocar."
        )
        self.status_var.set(
            "Exemplo pronto carregado. Se quiser criar uma pergunta nova, basta editar os campos livremente."
        )

    def _limpar_campos(self) -> None:
        """Limpa os textos informados pelo usuario sem alterar o modo atual."""
        if self.operacao_em_execucao:
            return
        for widget in (self.texto_pergunta, self.texto_esperada, self.texto_usuario):
            self._definir_texto(widget, "")
        self.indice_exemplo_atual = -1
        self.exemplo_info_var.set(
            "Campos limpos. Agora voce pode escrever uma pergunta nova sem depender dos exemplos."
        )
        self.status_var.set("Campos limpos. Pronto para montar uma nova avaliacao.")

    def _iniciar_avaliacao(self) -> None:
        """Valida os dados e dispara a avaliacao sem travar a interface."""
        if self.operacao_em_execucao:
            return

        pergunta = self._obter_texto(self.texto_pergunta)
        resposta_esperada = self._obter_texto(self.texto_esperada)
        resposta_usuario = self._obter_texto(self.texto_usuario)
        modo = self.modo_var.get()

        erro = self._validar_entradas(modo, pergunta, resposta_esperada, resposta_usuario)
        if erro:
            messagebox.showerror("Campos obrigatorios", erro)
            return

        self._alterar_estado_execucao(True, "Executando avaliacao. Aguarde um instante...")
        thread = threading.Thread(
            target=self._executar_avaliacao_em_thread,
            args=(modo, pergunta, resposta_esperada, resposta_usuario),
            daemon=True,
        )
        thread.start()

    def _validar_entradas(
        self,
        modo: str,
        pergunta: str,
        resposta_esperada: str,
        resposta_usuario: str,
    ) -> str | None:
        """Valida as entradas minimas para evitar erros triviais de uso."""
        if not pergunta.strip():
            return "A pergunta precisa ser informada para montar a avaliacao."
        if not resposta_esperada.strip():
            return "A resposta esperada e obrigatoria, porque ela funciona como gabarito da correcao."
        if modo == "topzera" and not resposta_usuario.strip():
            return "No Topzera a resposta do usuario nao pode ficar vazia."
        return None

    def _executar_avaliacao_em_thread(
        self,
        modo: str,
        pergunta: str,
        resposta_esperada: str,
        resposta_usuario: str,
    ) -> None:
        """Executa a avaliacao fora da thread principal da interface."""
        try:
            if modo == "mais_ou_menos":
                resultado = self._avaliar_mais_ou_menos(pergunta, resposta_esperada, resposta_usuario)
            else:
                resultado = self._avaliar_topzera(pergunta, resposta_esperada, resposta_usuario)
        except Exception as erro:
            LOGGER.exception("Falha ao executar avaliacao.")
            self.after(0, lambda: self._mostrar_erro(str(erro)))
            return

        self.after(0, lambda: self._renderizar_resultado(resultado))

    def _avaliar_mais_ou_menos(
        self,
        pergunta: str,
        resposta_esperada: str,
        resposta_usuario: str,
    ) -> ResultadoTela:
        """Executa o motor classico do projeto e adapta a saida para a GUI."""
        configuracao = ConfiguracaoAvaliacao(
            remover_stopwords=self.remover_stopwords_var.get(),
            aplicar_stemming=self.aplicar_stemming_var.get(),
        )
        resultado = avaliar_resposta(
            pergunta=pergunta,
            resposta_esperada=resposta_esperada,
            resposta_usuario=resposta_usuario,
            configuracao=configuracao,
        )

        linhas = [
            "Leitura principal",
            f"- Feedback: {formatar_feedback(resultado.feedback)}",
            f"- Nota final: {resultado.nota:.2f}/100",
            f"- Similaridade TF-IDF: {resultado.similaridade:.2%}",
            f"- Cobertura de palavras-chave: {resultado.cobertura_palavras_chave:.2%}",
            "",
            "Observacoes do motor",
        ]
        linhas.extend(
            f"- {observacao}" for observacao in resultado.observacoes
        )
        linhas.extend(
            [
                "",
                "Palavras-chave",
                f"- Esperadas: {', '.join(resultado.palavras_chave_esperadas) or 'nenhuma'}",
                f"- Encontradas: {', '.join(resultado.palavras_chave_encontradas) or 'nenhuma'}",
            ]
        )

        if self.mostrar_detalhes_var.get():
            linhas.extend(
                [
                    "",
                    "Camada tecnica",
                    (
                        "- Tokens da resposta esperada: "
                        + (" ".join(resultado.resposta_esperada_processada.tokens) or "nenhum")
                    ),
                    (
                        "- Tokens da resposta do usuario: "
                        + (" ".join(resultado.resposta_usuario_processada.tokens) or "nenhum")
                    ),
                    (
                        "- Radicais esperados: "
                        + (resultado.resposta_esperada_processada.texto_processado or "nenhum")
                    ),
                    (
                        "- Radicais do usuario: "
                        + (resultado.resposta_usuario_processada.texto_processado or "nenhum")
                    ),
                ]
            )

        resumo = (
            resultado.observacoes[0]
            if resultado.observacoes
            else "A nota foi calculada com base na combinacao entre proximidade textual e palavras-chave."
        )
        metricas = [
            ("Similaridade TF-IDF", f"{resultado.similaridade:.2%}"),
            ("Cobertura de palavras-chave", f"{resultado.cobertura_palavras_chave:.2%}"),
            (
                "Palavras-chave reconhecidas",
                f"{len(resultado.palavras_chave_encontradas)}/{len(resultado.palavras_chave_esperadas)}",
            ),
        ]
        return ResultadoTela(
            modo="Mais ou Menos",
            nota=resultado.nota,
            feedback=formatar_feedback(resultado.feedback),
            resumo=resumo,
            detalhes="\n".join(linhas),
            metricas=metricas,
        )

    def _avaliar_topzera(
        self,
        pergunta: str,
        resposta_esperada: str,
        resposta_usuario: str,
    ) -> ResultadoTela:
        """Executa o motor semantico e organiza a resposta para a GUI."""
        configuracao = carregar_configuracao()
        resultado = avaliar_resposta_com_ia(
            pergunta=pergunta,
            resposta_esperada=resposta_esperada,
            resposta_usuario=resposta_usuario,
            configuracao=configuracao,
        )

        linhas = [
            "Leitura principal",
            f"- Feedback: {formatar_feedback(resultado.feedback)}",
            f"- Nota final: {resultado.nota:.2f}/100",
            f"- Similaridade semantica: {resultado.similaridade_semantica:.2%}",
            f"- Deployment usado: {configuracao.deployment}",
            "",
            "Justificativa da IA",
            f"- {resultado.justificativa or 'A IA nao retornou justificativa textual.'}",
            "",
        ]

        linhas.extend(
            montar_bloco_lista(
                "Pontos corretos",
                resultado.pontos_corretos,
                "Nenhum ponto correto foi destacado.",
            )
        )
        linhas.append("")
        linhas.extend(
            montar_bloco_lista(
                "Lacunas",
                resultado.lacunas,
                "Nenhuma lacuna foi destacada.",
            )
        )
        linhas.append("")
        linhas.extend(
            montar_bloco_lista(
                "Alertas",
                resultado.alertas,
                "Nenhum alerta adicional foi identificado.",
            )
        )

        resumo = (
            resultado.justificativa
            or "A IA comparou o significado das duas respostas e sintetizou a proximidade semantica."
        )
        metricas = [
            ("Similaridade semantica", f"{resultado.similaridade_semantica:.2%}"),
            ("Pontos corretos", str(len(resultado.pontos_corretos))),
            ("Lacunas e alertas", str(len(resultado.lacunas) + len(resultado.alertas))),
        ]
        return ResultadoTela(
            modo="Topzera",
            nota=resultado.nota,
            feedback=formatar_feedback(resultado.feedback),
            resumo=resumo,
            detalhes="\n".join(linhas),
            metricas=metricas,
        )

    def _renderizar_resultado(self, resultado: ResultadoTela) -> None:
        """Atualiza todo o painel da direita com um novo resultado."""
        self._alterar_estado_execucao(False, f"{resultado.modo} concluiu a avaliacao com sucesso.")
        self.feedback_var.set(f"{resultado.modo}: {resultado.feedback}")
        self.resumo_var.set(resultado.resumo)
        self.label_feedback.configure(bg=cor_por_nota(resultado.nota))
        self._atualizar_metricas(resultado.metricas)
        self._atualizar_detalhes(resultado.detalhes)
        self._animar_nota(resultado.nota)

    def _mostrar_erro(self, mensagem: str) -> None:
        """Exibe falhas operacionais de forma clara para o usuario."""
        self._alterar_estado_execucao(False, "A avaliacao falhou. Revise a mensagem e tente novamente.")
        detalhe = mensagem.strip() or "Erro inesperado."
        self.feedback_var.set("Falha operacional")
        self.resumo_var.set(
            "Nao foi possivel concluir a avaliacao. O painel tecnico abaixo mostra a causa reportada pelo motor."
        )
        self.label_feedback.configure(bg=CORES["coral"])
        self._atualizar_metricas(
            [
                ("Status", "Erro"),
                ("Modo ativo", "Topzera" if self.modo_var.get() == "topzera" else "Mais ou Menos"),
                ("Acao sugerida", "Revisar configuracao"),
            ]
        )
        self._atualizar_detalhes(f"Falha reportada\n- {detalhe}")
        self._animar_nota(0.0)
        messagebox.showerror("Falha na avaliacao", detalhe)

    def _verificar_configuracao_azure(self) -> None:
        """Valida a configuracao do Azure em segundo plano."""
        if self.operacao_em_execucao:
            return

        self._alterar_estado_execucao(True, "Validando configuracao do Azure OpenAI...")
        thread = threading.Thread(target=self._executar_check_azure_em_thread, daemon=True)
        thread.start()

    def _executar_check_azure_em_thread(self) -> None:
        """Executa o check de configuracao do Azure fora da thread da interface."""
        try:
            configuracao = carregar_configuracao()
        except Exception as erro:
            LOGGER.exception("Falha ao verificar configuracao do Azure.")
            self.after(0, lambda: self._finalizar_check_azure(False, str(erro)))
            return

        mensagem = (
            f"Configuracao valida. Deployment: {configuracao.deployment}. "
            f"API version: {configuracao.api_version}. Endpoint: {configuracao.endpoint}"
        )
        self.after(0, lambda: self._finalizar_check_azure(True, mensagem))

    def _finalizar_check_azure(self, sucesso: bool, mensagem: str) -> None:
        """Atualiza a UI apos a verificacao de credenciais do Azure."""
        self._alterar_estado_execucao(False, "Check de configuracao finalizado.")
        self.azure_status_var.set(mensagem)
        if sucesso:
            messagebox.showinfo("Azure OpenAI", mensagem)
        else:
            messagebox.showerror("Azure OpenAI", mensagem)

    def _alterar_estado_execucao(self, ativo: bool, mensagem: str) -> None:
        """Liga ou desliga o estado de carregamento da tela."""
        self.operacao_em_execucao = ativo
        self.status_var.set(mensagem)

        estado = "disabled" if ativo else "normal"
        for widget in (
            self.botao_avaliar,
            self.botao_limpar,
            self.botao_carregar,
            self.botao_check_azure,
            self.botao_mais_ou_menos,
            self.botao_topzera,
        ):
            widget.configure(state=estado)

        if ativo:
            self.progressbar.start(12)
        else:
            self.progressbar.stop()

    def _atualizar_metricas(self, metricas: list[tuple[str, str]]) -> None:
        """Renderiza as tres metricas resumidas do resultado atual."""
        preenchidas = list(metricas[:3])
        while len(preenchidas) < 3:
            preenchidas.append(("Indicador", "--"))

        for indice, (titulo, valor) in enumerate(preenchidas):
            self.metricas_titulos[indice].set(titulo)
            self.metricas_valores[indice].set(valor)

    def _atualizar_detalhes(self, texto: str) -> None:
        """Atualiza a area rolavel com a explicacao tecnica da avaliacao."""
        self.texto_detalhes.configure(state="normal")
        self.texto_detalhes.delete("1.0", "end")
        self.texto_detalhes.insert("1.0", texto.strip())
        self.texto_detalhes.configure(state="disabled")

    def _animar_nota(self, destino: float) -> None:
        """Anima o medidor para deixar a leitura mais viva e intuitiva."""
        destino = max(0.0, min(100.0, destino))
        if self.animacao_id:
            self.after_cancel(self.animacao_id)
            self.animacao_id = None
        self._animar_passo(destino)

    def _animar_passo(self, destino: float) -> None:
        """Executa um passo da animacao do medidor."""
        delta = destino - self.nota_animada
        if abs(delta) < 0.35:
            self.nota_animada = destino
            self._desenhar_medidor(self.nota_animada)
            self.animacao_id = None
            return

        self.nota_animada += delta * 0.18
        self._desenhar_medidor(self.nota_animada)
        self.animacao_id = self.after(16, lambda: self._animar_passo(destino))

    def _desenhar_medidor(self, nota: float) -> None:
        """Desenha um placar com barra horizontal para representar a nota."""
        canvas = self.canvas_medidor
        canvas.delete("all")

        cor_nota = cor_por_nota(nota)
        barra_x0 = 184
        barra_x1 = 418
        barra_y0 = 64
        barra_y1 = 82
        progresso = max(0.0, min(1.0, nota / 100))
        largura_preenchida = (barra_x1 - barra_x0) * progresso

        canvas.create_text(88, 58, text=f"{nota:.0f}", fill=CORES["texto"], font=FONTES["placar"])
        canvas.create_text(88, 92, text="pontos", fill=CORES["texto_suave"], font=FONTES["placar_legenda"])
        canvas.create_text(
            88,
            116,
            text="Aderencia ao gabarito",
            fill=CORES["texto_suave"],
            font=FONTES["subtitulo"],
            width=120,
        )
        canvas.create_line(150, 28, 150, 138, fill=CORES["borda"], width=2)

        self._desenhar_capsula(canvas, barra_x0, barra_y0, barra_x1, barra_y1, CORES["cinza"])
        if largura_preenchida > 0:
            self._desenhar_capsula(
                canvas,
                barra_x0,
                barra_y0,
                barra_x0 + largura_preenchida,
                barra_y1,
                cor_nota,
            )

        canvas.create_text(barra_x0, 102, text="0", fill=CORES["texto_suave"], font=FONTES["placar_legenda"], anchor="w")
        canvas.create_text(barra_x1, 102, text="100", fill=CORES["texto_suave"], font=FONTES["placar_legenda"], anchor="e")
        canvas.create_text(
            (barra_x0 + barra_x1) / 2,
            122,
            text=f"{nota:.1f}% de aderencia estimada",
            fill=CORES["texto"],
            font=FONTES["corpo_negrito"],
        )
        canvas.create_text(
            (barra_x0 + barra_x1) / 2,
            146,
            text="Quanto maior, mais proxima a resposta ficou do gabarito.",
            fill=CORES["texto_suave"],
            font=FONTES["subtitulo"],
            width=250,
        )

    def _desenhar_capsula(
        self,
        canvas: tk.Canvas,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        cor: str,
    ) -> None:
        """Desenha uma barra com extremidades arredondadas no canvas."""
        if x1 <= x0:
            return

        raio = (y1 - y0) / 2
        if (x1 - x0) <= (2 * raio):
            canvas.create_oval(x0, y0, x1, y1, fill=cor, outline=cor)
            return

        canvas.create_rectangle(x0 + raio, y0, x1 - raio, y1, fill=cor, outline=cor)
        canvas.create_oval(x0, y0, x0 + (2 * raio), y1, fill=cor, outline=cor)
        canvas.create_oval(x1 - (2 * raio), y0, x1, y1, fill=cor, outline=cor)

    def _obter_texto(self, widget: CampoEntrada) -> str:
        """L o conteudo atual de um campo de entrada."""
        if isinstance(widget, tk.Entry):
            return widget.get().strip()
        return widget.get("1.0", "end").strip()

    def _definir_texto(self, widget: CampoEntrada, texto: str) -> None:
        """Substitui o conteudo de um campo de entrada."""
        if isinstance(widget, tk.Entry):
            widget.delete(0, "end")
            widget.insert(0, texto)
            return
        widget.delete("1.0", "end")
        widget.insert("1.0", texto)


def main() -> None:
    """Ponto de entrada da interface grafica."""
    app = DidItUnderstandGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
