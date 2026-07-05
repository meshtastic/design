import StyleDictionary from 'style-dictionary';
import { promises as fs } from 'node:fs';
import path from 'node:path';

// ponytail: custom action because Apple consumes named asset colorsets (light/dark),
// not Swift color literals. One <Name>.colorset/Contents.json per theme.* role.
// ceiling: colors only; sizing/type still need custom transforms (see README).
const noTheme = (t) => t.path[0] !== 'theme';
const pascal = (s) => s.split('-').map((w) => w[0].toUpperCase() + w.slice(1)).join('');
const components = (hex) => {
  const h = hex.replace('#', '');
  return {
    red: `0x${h.slice(0, 2).toUpperCase()}`,
    green: `0x${h.slice(2, 4).toUpperCase()}`,
    blue: `0x${h.slice(4, 6).toUpperCase()}`,
    alpha: '1.000',
  };
};
const entry = (hex, dark) => ({
  idiom: 'universal',
  ...(dark ? { appearances: [{ appearance: 'luminosity', value: 'dark' }] } : {}),
  color: { 'color-space': 'srgb', components: components(hex) },
});

StyleDictionary.registerAction({
  name: 'ios/colorsets',
  do: async (dictionary, config) => {
    const roles = {};
    for (const t of dictionary.allTokens) {
      if (t.path[0] !== 'theme') continue;
      const [, role, mode] = t.path;
      (roles[role] ??= {})[mode] = t.original?.$value ?? t.$value;
    }
    for (const [role, m] of Object.entries(roles)) {
      const contents = {
        colors: [entry(m.light, false), entry(m.dark ?? m.light, true)],
        info: { author: 'xcode', version: 1 },
      };
      const dir = path.join(config.buildPath, `Meshtastic${pascal(role)}.colorset`);
      await fs.mkdir(dir, { recursive: true });
      await fs.writeFile(path.join(dir, 'Contents.json'), JSON.stringify(contents, null, 2) + '\n');
    }
  },
  undo: async () => {},
});

const sd = new StyleDictionary({
  source: ['tokens.json'],
  platforms: {
    css: {
      transformGroup: 'css',
      buildPath: 'build/css/',
      files: [{ destination: 'tokens.css', format: 'css/variables', filter: noTheme }],
    },
    compose: {
      transformGroup: 'compose',
      buildPath: 'build/compose/',
      files: [{
        destination: 'MeshtasticTokens.kt',
        format: 'compose/object',
        filter: noTheme,
        options: { className: 'MeshtasticTokens', packageName: 'org.meshtastic.design.tokens' },
      }],
    },
    ios: {
      transformGroup: 'js',
      buildPath: 'build/ios/Colors/',
      files: [],
      actions: ['ios/colorsets'],
    },
  },
});

await sd.buildAllPlatforms();
console.log('✔︎ css + compose + ios colorsets');
