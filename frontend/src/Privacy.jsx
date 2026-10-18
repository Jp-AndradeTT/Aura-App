// ATENÇÃO: este texto é um MODELO para profissional autônoma (sem CNPJ) baseado na LGPD (Lei 13.709/2018). Preencha os campos [entre colchetes],
// confira se descreve o que o sistema realmente faz e peça revisão de um advogado antes de publicar.
// Se mudar o texto, atualize POLICY_VERSION em backend/app.py.
export const POLICY_VERSION = "1.5";
const UPDATED = "[DD/MM/AAAA]";

const SECTIONS = [
  ["1. Quem somos", [
    "O Aura (o “serviço”) é uma ferramenta de apoio ao trabalho de [NOME COMPLETO DA MENTORA], profissional autônoma de mentoria financeira, que é a controladora dos dados pessoais tratados no serviço. O serviço é oferecido aos clientes da mentoria.",
    "Para exercer seus direitos ou tirar dúvidas sobre seus dados, escreva para [E-MAIL DE CONTATO DA MENTORA].",
  ]],
  ["2. O que o serviço é", [
    "O Aura é uma ferramenta educativa de organização financeira: lê sua fatura, calcula parcelas e projeções e sugere um plano para formar reserva.",
    "O serviço não é consultoria de investimentos nem substitui um profissional certificado. Os planos e as respostas da Aura (chat) são gerados por inteligência artificial, não por uma pessoa, e podem conter erros: confira os valores e decida com cautela.",
  ]],
  ["3. Dados que coletamos", [
    "- Cadastro: nome, e-mail e senha. A senha é guardada apenas em formato criptográfico irreversível (hash).",
    "- Dados financeiros que você informa ou confirma: lançamentos da fatura (descrição, categoria, valor e parcelas), banco ou cartão, renda mensal, gastos fixos, meta de reserva e dia de vencimento.",
    "- Resultados gerados: análises, projeções e planos, além do histórico das suas faturas.",
    "- Conversas com a Aura (chat): suas mensagens são enviadas ao provedor de IA para gerar a resposta e não são guardadas por nós; a conversa some ao fechar a página.",
    "- Dados técnicos: endereço IP, data e hora de acesso e registros de segurança, como tentativas de login.",
    "- Verificação em duas etapas (opcional): o segredo do aplicativo autenticador, criptografado, e códigos de recuperação guardados apenas como hash.",
    "- Recuperação de senha: um código temporário de uso único, guardado apenas em forma de hash, que expira em 30 minutos.",
    "Não pedimos nem guardamos número completo do cartão, código de segurança, senhas de banco ou CPF. O arquivo da fatura (PDF ou foto) é usado só para extrair os lançamentos e não é armazenado por nós. Se possível, oculte dados pessoais desnecessários antes de enviar.",
  ]],
  ["4. Para que usamos e em que base legal", [
    "- Criar e manter sua conta, calcular e guardar seu histórico, gerar planos e planilhas: execução do contrato (LGPD, art. 7º, V).",
    "- Enviar os dados da fatura e do seu perfil à IA para leitura e geração do plano: seu consentimento (art. 7º, I), que você pode revogar a qualquer momento.",
    "- Segurança, prevenção a fraudes e abuso: legítimo interesse (art. 7º, IX).",
    "- Guarda de registros de acesso: cumprimento de obrigação legal (art. 7º, II; Marco Civil da Internet, art. 15).",
    "Dados financeiros não são classificados como sensíveis pela LGPD, mas os tratamos com cuidado reforçado. Não usamos seus dados para publicidade nem os vendemos.",
  ]],
  ["5. Com quem compartilhamos", [
    "Compartilhamos dados somente com prestadores que nos ajudam a operar o serviço, nos limites necessários:",
    "- Provedor de inteligência artificial (Anthropic, PBC): recebe os dados da fatura e do perfil para extrair lançamentos e gerar o plano. [Confirme as condições de retenção e uso de dados vigentes no contrato com o provedor.]",
    "- Hospedagem e banco de dados (Render Services, Inc.).",
    "- Rede e segurança (Cloudflare, Inc.).",
    "- Envio de e-mails de recuperação de senha e avisos de segurança: [provedor de e-mail utilizado, ex.: Google (Gmail), Brevo ou Resend].",
    "Também podemos compartilhar dados para cumprir ordem legal ou judicial.",
  ]],
  ["6. Transferência internacional", [
    "Alguns prestadores operam fora do Brasil, inclusive nos Estados Unidos. Adotamos as garantias previstas na LGPD (art. 33) para essas transferências. [Informe a região dos servidores.]",
  ]],
  ["7. Por quanto tempo guardamos", [
    "Guardamos seus dados enquanto sua conta estiver ativa. Ao excluir a conta, apagamos cadastro, faturas e planos em até [30] dias, incluindo cópias de segurança.",
    "Registros de acesso são mantidos por 6 meses, conforme o Marco Civil da Internet.",
  ]],
  ["8. Seus direitos", [
    "Você pode, a qualquer momento: confirmar que tratamos seus dados; acessá-los; corrigi-los; pedir anonimização, bloqueio ou eliminação; pedir portabilidade; saber com quem compartilhamos; revogar o consentimento; e se opor a tratamento irregular (LGPD, art. 18).",
    "No aplicativo, use “Exportar meus dados” e “Excluir minha conta”. Para outros pedidos, escreva para [E-MAIL DE CONTATO DA MENTORA]. Você também pode reclamar à Autoridade Nacional de Proteção de Dados (ANPD).",
    "Se discordar de um resultado gerado por IA, você pode pedir revisão por uma pessoa.",
  ]],
  ["9. Como protegemos seus dados", [
    "- Conexão criptografada (HTTPS) e senhas guardadas apenas como hash.",
    "- Dados financeiros (lançamentos, renda, gastos e planos) criptografados no banco de dados.",
    "- Isolamento por conta: cada usuário só acessa as próprias faturas.",
    "- Confirmação do e-mail no cadastro e verificação em duas etapas opcional.",
    "- Limite diário de uso da IA por conta, para evitar abuso.",
    "- Bloqueio temporário após tentativas de login incorretas e limite de pedidos por período.",
    "- Sessão em cookie protegido, com prazo de validade; você pode sair de todos os dispositivos e somos avisados de alterações de senha por e-mail.",
    "Nenhum sistema é totalmente imune a falhas. Em caso de incidente relevante, avisaremos você e a ANPD conforme a lei.",
  ]],
  ["10. Cookies", [
    "Usamos apenas um cookie de sessão, estritamente necessário para mantê-lo conectado (HttpOnly e com prazo de validade). Não usamos cookies de publicidade ou rastreamento.",
  ]],
  ["11. Menores de idade", ["O serviço é destinado a maiores de 18 anos."]],
  ["12. Mudanças nesta política", [
    "Podemos atualizar esta política. A versão e a data ficam no topo da página, e avisaremos no serviço quando a mudança for relevante.",
  ]],
];

export default function Privacy({ back, onTerms }) {
  return (
    <article className="policy">
      <button className="btn ghost" onClick={back}>Voltar</button>
      <h2 style={{ marginTop: 20 }}>Política de Privacidade</h2>
      <p className="lead">Versão {POLICY_VERSION}, atualizada em {UPDATED}</p>
      {onTerms && <p><button className="link" onClick={onTerms}>Ver Termos de Uso</button></p>}
      {SECTIONS.map(([title, lines]) => (
        <section key={title}>
          <h3>{title}</h3>
          {lines.map((l, i) => (l.startsWith("- ") ? <p key={i} className="bul">{l.slice(2)}</p> : <p key={i}>{l}</p>))}
        </section>
      ))}
    </article>
  );
}
