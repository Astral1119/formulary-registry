import AdmZip from 'adm-zip';
import fs from 'fs-extra';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const REGISTRY_ROOT = path.resolve(__dirname, '../../');
const SITE_ROOT = path.resolve(__dirname, '../');
const CONTENT_DIR = path.join(SITE_ROOT, 'src/content/packages');

async function extractDocs() {
    const indexJsonPath = path.join(REGISTRY_ROOT, 'index.json');
    const registry = await fs.readJson(indexJsonPath);

    await fs.ensureDir(CONTENT_DIR);
    await fs.emptyDir(CONTENT_DIR);

    for (const [pkgName, pkgData] of Object.entries(registry)) {
        for (const [version, versionData] of Object.entries(pkgData.versions)) {
            const gspkgPath = path.join(REGISTRY_ROOT, versionData.path);
            const outputDir = path.join(CONTENT_DIR, pkgName, version);
            await fs.ensureDir(outputDir);

            if (!await fs.pathExists(gspkgPath)) {
                console.warn(`Warning: ${gspkgPath} not found.`);
                continue;
            }

            const zip = new AdmZip(gspkgPath);
            const zipEntries = zip.getEntries();

            let readmeContent = '';
            let hasDocs = false;

            // extract readme.md and project config
            const readmeEntry = zipEntries.find(e => e.entryName.toLowerCase() === 'readme.md');
            if (readmeEntry) {
                readmeContent = readmeEntry.getData().toString('utf8');
            }

            let projectConfig = {};
            const projectEntry = zipEntries.find(e => e.entryName.toLowerCase() === '__gsproject__.json');
            if (projectEntry) {
                try {
                    projectConfig = JSON.parse(projectEntry.getData().toString('utf8'));
                } catch (e) {
                    console.warn(`failed to parse __GSPROJECT__.json for ${pkgName}@${version}`);
                }
            }

            // extract functions.json
            let functionsData = null;
            const functionsEntry = zipEntries.find(e => e.entryName.toLowerCase() === 'functions.json');
            if (functionsEntry) {
                try {
                    functionsData = JSON.parse(functionsEntry.getData().toString('utf8'));
                } catch (e) {
                    console.warn(`failed to parse functions.json for ${pkgName}@${version}`);
                }
            }

            // extract docs/ folder
            zipEntries.forEach(entry => {
                if (entry.entryName.startsWith('docs/') && !entry.isDirectory) {
                    const relativePath = entry.entryName.substring(5);
                    const targetPath = path.join(outputDir, 'docs', relativePath);
                    fs.ensureDirSync(path.dirname(targetPath));
                    fs.writeFileSync(targetPath, entry.getData());
                    hasDocs = true;
                }
            });

            const isLatest = pkgData.latest === version;

            // build search index
            let searchIndexParts = [pkgName, pkgData.description];
            if (projectConfig.keywords) searchIndexParts.push(projectConfig.keywords);
            if (functionsData) {
                for (const [funcName, funcDef] of Object.entries(functionsData)) {
                    searchIndexParts.push(funcName);
                    if (funcDef.description) searchIndexParts.push(funcDef.description);
                }
            }
            const searchIndex = searchIndexParts.join(' ').replace(/\s+/g, ' ').trim();

            // normalize keywords
            let keywords = projectConfig.keywords || '';
            if (Array.isArray(keywords)) {
                keywords = keywords.join(', ');
            } else if (typeof keywords === 'string' && keywords.startsWith('[') && keywords.endsWith(']')) {
                // handle string-encoded arrays like "['a', 'b']"
                try {
                    // try to parse as json first, but it might use single quotes
                    const sanitized = keywords.replace(/'/g, '"');
                    const parsed = JSON.parse(sanitized);
                    if (Array.isArray(parsed)) {
                        keywords = parsed.join(', ');
                    }
                } catch (e) {
                    // if parsing fails, just keep as is or strip brackets
                    keywords = keywords.slice(1, -1).split(',').map(k => k.trim().replace(/^['"]|['"]$/g, '')).join(', ');
                }
            }
            projectConfig.keywords = keywords;

            // synthesize readme if missing
            if (!readmeContent) {
                readmeContent = synthesizeReadme(pkgName, version, pkgData, versionData, functionsData, projectConfig, searchIndex, isLatest);
            } else {
                // prepend frontmatter for existing readme
                const frontmatter = `---
title: ${pkgName}
version: ${version}
description: ${pkgData.description}
latest: ${isLatest}${projectConfig.keywords ? `\nkeywords: ${projectConfig.keywords}` : ''}${projectConfig.homepage ? `\nhomepage: ${projectConfig.homepage}` : ''}${projectConfig.license ? `\nlicense: ${projectConfig.license}` : ''}
searchIndex: "${searchIndex.replace(/"/g, '\\"')}"
dependencies: ${JSON.stringify(versionData.dependencies)}
---

`;
                readmeContent = frontmatter + readmeContent;
                if (functionsData) {
                    readmeContent += `\n\n${generateApiDocs(functionsData)}`;
                }
            }

            // write readme.md
            await fs.writeFile(path.join(outputDir, 'index.md'), readmeContent);

            // write metadata
            const metadata = {
                name: pkgName,
                version: version,
                description: pkgData.description,
                owners: pkgData.owners,
                dependencies: versionData.dependencies,
                latest: isLatest,
                hasDocs,
                keywords: projectConfig.keywords,
                homepage: projectConfig.homepage,
                license: projectConfig.license,
                searchIndex: searchIndex,
                functions: functionsData
            };
            await fs.writeJson(path.join(outputDir, 'metadata.json'), metadata);
        }
    }
}

function synthesizeReadme(name, version, pkgData, versionData, functionsData, projectConfig, searchIndex, isLatest) {
    const deps = versionData.dependencies.length > 0
        ? versionData.dependencies.map(d => {
            const match = d.match(/^([a-z0-9-]+)(?:>=|@)?(.*)$/i);
            const depName = match ? match[1] : d;
            return `- [${d}](/packages/${depName})`;
        }).join('\n')
        : '_No dependencies_';

    return `---
title: ${name}
version: ${version}
description: ${pkgData.description}
latest: ${isLatest}${projectConfig.keywords ? `\nkeywords: ${projectConfig.keywords}` : ''}${projectConfig.homepage ? `\nhomepage: ${projectConfig.homepage}` : ''}${projectConfig.license ? `\nlicense: ${projectConfig.license}` : ''}
searchIndex: "${searchIndex.replace(/"/g, '\\"')}"
dependencies: ${JSON.stringify(versionData.dependencies)}
---

${generateApiDocs(functionsData)}

<div class="auto-doc-callout">
This package does not have a custom README. This page was automatically generated from package metadata.
</div>
`;
}

function generateApiDocs(functionsData) {
    if (!functionsData) return '';

    let docs = '## API Reference\n\n';
    for (const [funcName, funcDef] of Object.entries(functionsData)) {
        docs += `### \`${funcName}\`\n\n`;
        docs += `${funcDef.description || 'No description provided.'}\n\n`;

        if (funcDef.arguments && Object.keys(funcDef.arguments).length > 0) {
            docs += '**Arguments**:\n';
            for (const [argName, argDef] of Object.entries(funcDef.arguments)) {
                docs += `- \`${argName}\`: ${argDef.description || ''}\n`;
            }
            docs += '\n';
        }
    }
    return docs;
}

extractDocs().catch(console.error);
