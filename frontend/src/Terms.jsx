// ATENÇÃO: MODELO de Termos de Uso para profissional autônoma (sem CNPJ). Preencha os campos [entre colchetes],
// confira se descrevem o que o serviço realmente faz e peça revisão de um advogado antes de publicar.
// Se mudar o texto, atualize POLICY_VERSION (em Privacy.jsx e backend/app.py): o aceite registra essa versão.
import { POLICY_VERSION } from "./Privacy";

const SECTIONS = [
  ["1. Sobre o serviço", [
    "O Aura é uma ferramenta de apoio à mentoria financeira de [NOME COMPLETO DA MENTORA] (“mentora”). Ele lê a fatura do cartão que você envia, organiza os lançamentos, projeta as parcelas dos próximos meses e sugere um plano para formar reserva.",
    "O serviço é oferecido aos clientes da mentoria. Ao criar a conta ou usar o serviço, você aceita estes Termos e a Política de Privacidade.",
  ]],
  ["2. Natureza educativa", [
    "O Aura oferece orientação educativa. Não é consultoria de investimentos, de crédito, jurídica ou tributária e não substitui um profissional habilitado.",
    "Os números são estimativas feitas com os dados que você informou ou confirmou. As decisões financeiras são suas.",
  ]],
  ["3. Cadastro e conta", [
    "Você declara ter 18 anos ou mais e informar dados verdadeiros. A conta é pessoal e a senha é intransferível: não a compartilhe.",
    "Recomendamos ativar a verificação em duas etapas em “Minha conta”. Se suspeitar de uso indevido da sua conta, altere a senha, saia de todos os dispositivos e avise a mentora.",
  ]],
  ["4. Uso adequado", [
    "Envie apenas faturas e dados seus, ou de quem autorizou você. É proibido tentar burlar a segurança, sobrecarregar o serviço, acessar dados de outras pessoas ou usá-lo para fins ilícitos.",
  ]],
  ["5. Inteligência artificial", [
    "A leitura das faturas e as respostas da Aura (plano e chat) são geradas por inteligência artificial e podem conter erros. Confira os lançamentos lidos e os valores antes de decidir.",
    "Há limites diários e mensais de uso da IA. Quando atingidos, você pode digitar os lançamentos manualmente e usar o plano padrão.",
  ]],
  ["6. Dados pessoais", ["O tratamento dos seus dados está descrito na Política de Privacidade."]],
  ["7. Disponibilidade", [
    "Trabalhamos para manter o serviço disponível, mas ele pode ficar indisponível por manutenção, falhas de terceiros ou motivos fora do nosso controle. Não garantimos resultados financeiros.",
  ]],
  ["8. Responsabilidade", [
    "Na medida permitida pela lei, inclusive pelo Código de Defesa do Consumidor quando aplicável, a mentora não responde por decisões tomadas com base nas estimativas do serviço. Nada nestes Termos exclui responsabilidades que a lei não permite excluir.",
  ]],
  ["9. Valores e pagamento", [
    "[Descreva: serviço incluído na mentoria / valor, forma e periodicidade de pagamento, renovação e política de reembolso.]",
  ]],
  ["10. Cancelamento e exclusão", [
    "Você pode excluir a conta a qualquer momento em “Minha conta”, o que apaga seus dados conforme a Política de Privacidade. Podemos suspender contas que violem estes Termos.",
  ]],
  ["11. Propriedade intelectual", [
    "O software e a marca Aura pertencem a [NOME COMPLETO DA MENTORA / TITULAR]. Os dados que você envia continuam sendo seus.",
  ]],
  ["12. Alterações", [
    "Podemos atualizar estes Termos. A versão e a data ficam no topo da página, e pediremos novo aceite quando a mudança for relevante.",
  ]],
  ["13. Lei e foro", [
    "Estes Termos seguem a lei brasileira. Para consumidores, vale o foro do domicílio do consumidor; nos demais casos, o foro de [CIDADE/UF].",
  ]],
  ["14. Contato", ["Dúvidas ou pedidos: [E-MAIL DE CONTATO DA MENTORA]."]],
];

export default function Terms({ back, onPolicy }) {
  return (
    <article className="policy">
      <button className="btn ghost" onClick={back}>Voltar</button>
      <h2 style={{ marginTop: 20 }}>Termos de Uso</h2>
      <p className="lead">Versão {POLICY_VERSION}, atualizada em [DD/MM/AAAA]</p>
      <p><button className="link" onClick={onPolicy}>Ver Política de Privacidade</button></p>
      {SECTIONS.map(([title, lines]) => (
        <section key={title}><h3>{title}</h3>{lines.map((l, i) => <p key={i}>{l}</p>)}</section>
      ))}
    </article>
  );
}
