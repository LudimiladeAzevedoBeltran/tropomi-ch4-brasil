# Limpeza de Git (Google Drive)

Utilitário para manter um repositório Git que mora **dentro do Google Drive**.

## Por que isso existe

O Google Drive cria um arquivo `desktop.ini` em **todas** as pastas que sincroniza —
inclusive **dentro da pasta `.git`** (em `.git/refs/`, `.git/objects/`, `.git/logs/`...).

O Git não espera esses arquivos ali e pode quebrar com erros como:

```
fatal: bad object refs/desktop.ini
```

que aparecem ao rodar `git log --all`, `git fsck`, `git remote show`, etc.

A solução é **remover os `desktop.ini` de dentro do `.git`** e conferir a integridade.
O Drive vai recriá-los com o tempo, então vale rodar a limpeza de vez em quando.

## Pré-requisitos

- Windows com **PowerShell** (já vem instalado).
- **Git** instalado — serve o do **GitHub Desktop** ou o **Git for Windows**.
  O script procura os dois automaticamente.

## Passo a passo

1. Abra a pasta `limpeza-de-git` no Explorador de Arquivos.
2. Clique com o botão direito em um espaço vazio → **"Abrir no Terminal"**
   (ou **"Abrir janela do PowerShell aqui"**).
3. Rode o comando:

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\limpar_repo.ps1
   ```

   > Também funciona: clique com o botão direito no arquivo `limpar_repo.ps1` →
   > **Executar com PowerShell**.

4. Leia a saída. O esperado é terminar com algo como:

   ```
   OK: repositorio integro.
   ...
   Concluido.
   ```

O script assume que o repositório é a **pasta-mãe** de `limpeza-de-git`. Se quiser
apontar para outro lugar, use `-Repo`:

```powershell
.\limpar_repo.ps1 -Repo "C:\caminho\do\repositorio"
```

## O que o script faz

1. Localiza o executável do Git.
2. Remove todos os `desktop.ini` de dentro da pasta `.git`.
3. Roda `git fsck --full` para verificar a integridade.
4. Mostra `git show-ref` (refs), `git remote -v` (remoto) e `git status`.

Nada é enviado para o GitHub nem apagado do seu código: ele mexe **só** nos
`desktop.ini` internos do `.git`.

## Quando rodar

- Quando algum comando do Git der erro estranho (ex.: `bad object refs/desktop.ini`).
- De vez em quando, como manutenção (o Drive reinjeta os arquivos com o tempo).

## Dica

Se um dia quiser evitar o problema de vez, mova o repositório para **fora** do
Google Drive (ex.: `C:\Users\<você>\repos\`). Enquanto ele ficar no Drive, é só
rodar este script periodicamente.
