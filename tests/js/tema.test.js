const test = require('node:test');
const assert = require('node:assert/strict');
const T = require('../../site/assets/js/tema.js');
const fs = require('node:fs');
const path = require('node:path');

const CHAVES = ['bg', 'surface', 'surface2', 'ink', 'muted', 'line', 'brand', 'brand-ink', 'brand-soft', 'hl', 'hl-ink', 'hl-soft', 'warn', 'warn-soft', 'focus'];
const tokens = JSON.parse(fs.readFileSync(path.join(__dirname, '../../design-system/orgatec-trilha/tokens.json'), 'utf8'));

test('as 7 paletas do ORGATEC Trilha estão completas e iguais ao tokens.json', () => {
  assert.deepEqual(Object.keys(T.TEMAS), tokens.color.themes.map((t) => t.id));
  for (const [id, t] of Object.entries(T.TEMAS)) {
    for (const k of CHAVES) {
      assert.match(t.cores[k], /^#[0-9a-fA-F]{6}$/, id + ' ' + k);
      assert.equal(t.cores[k], tokens.color.tokens.find((x) => x.name === k).value[id], id + ' ' + k);
    }
  }
  assert.equal(T.TEMAS['azul-fl-esc'].escuro, true);
  assert.equal(T.TEMAS['azul-fl-esc'].flutuante, true);
  assert.equal(T.TEMAS.verde.escuro, false);
  assert.equal(T.TEMAS.noite.flutuante, false);
});

test('padrão, Automático e id desconhecido', () => {
  assert.equal(T.PADRAO, 'azul-fl-esc'); // escolha da ORGATEC em 02/11/2026
  assert.equal(T.resolver('auto', false), 'verde');
  assert.equal(T.resolver('auto', true), 'noite');
  assert.equal(T.resolver('inexistente', false), 'azul-fl-esc');
  assert.equal(T.resolver('vinho', true), 'vinho');
  assert.equal(T.ORDEM.length, 8);
  assert.equal(T.nome('auto'), 'Automático');
  assert.equal(T.nome('azul'), 'Azul Tribunal');
});

test('o CSS do site começa na paleta padrão (sem piscar antes do tema.js)', () => {
  const css = fs.readFileSync(path.join(__dirname, '../../site/assets/css/orgatec.css'), 'utf8');
  assert.match(css, new RegExp('--bg:' + T.TEMAS['azul-fl-esc'].cores.bg + ';'));
  assert.match(css, /color-scheme:dark;/);
  assert.match(css, /--acao:var\(--brand\)/); // componentes og-* leem as cores do Trilha
  assert.match(css, /--contato:#10b981/); // verde reservado ao WhatsApp
});
