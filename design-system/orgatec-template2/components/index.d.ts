import type * as React from 'react';
/** Logotipo ORGATEC: símbolo de 4 faixas + nome. Fundo claro: tom 'claro'. Fundo escuro: tom 'escuro' (símbolo branco). */
export interface AssinaturaProps { variante?: 'horizontal' | 'vertical' | 'reduzida'; tom?: 'claro' | 'escuro'; descritor?: boolean; altura?: number; className?: string }
export declare function Assinatura(props: AssinaturaProps): React.ReactElement;
/** Botão ou link (com href). 'contato' é exclusivo do WhatsApp; 'sobre-palco' só sobre o hero escuro. */
export interface BotaoProps extends React.ButtonHTMLAttributes<HTMLButtonElement> { variante?: 'primario' | 'contato' | 'contorno' | 'sobre-palco'; tamanho?: 'md' | 'lg'; href?: string; children?: React.ReactNode }
export declare function Botao(props: BotaoProps): React.ReactElement;
/** Selo de estado. Sem children, 'pendente' escreve "pendente de validação". */
export interface SeloProps { tom?: 'pendente' | 'definido' | 'futuro' | 'norma'; children?: React.ReactNode; className?: string }
export declare function Selo(props: SeloProps): React.ReactElement;
/** Citação de norma com link oficial; validado=false acrescenta o selo pendente. */
export interface CitacaoFonteProps { rotulo: string; url?: string; validado?: boolean; className?: string }
export declare function CitacaoFonte(props: CitacaoFonteProps): React.ReactElement;
/** Cartão do Hub: referência legal em mono, título e resumo. */
export interface CartaoHubProps { referencia?: string; titulo: string; href?: string; pendente?: boolean; children?: React.ReactNode; className?: string }
export declare function CartaoHub(props: CartaoHubProps): React.ReactElement;
/** Rótulo + campo (input, ou select com opcoes) + ajuda ou erro. id é obrigatório. */
export interface CampoProps extends React.InputHTMLAttributes<HTMLInputElement> { id: string; rotulo: string; ajuda?: string; erro?: string; tamanho?: 'md' | 'lg'; opcoes?: { valor: string; rotulo: string }[] }
export declare function Campo(props: CampoProps): React.ReactElement;
/** Caixa de consentimento LGPD. Nunca pré-marcada. */
export interface ConsentimentoProps extends React.InputHTMLAttributes<HTMLInputElement> { children: React.ReactNode }
export declare function Consentimento(props: ConsentimentoProps): React.ReactElement;
declare global { interface Window { OrgatecUI: { Assinatura: typeof Assinatura; Botao: typeof Botao; Selo: typeof Selo; CitacaoFonte: typeof CitacaoFonte; CartaoHub: typeof CartaoHub; Campo: typeof Campo; Consentimento: typeof Consentimento } } }
