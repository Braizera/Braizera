  ### Hi, I’m Braz Junior 👋
 
[![Blog](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/braz-calixto-de-souza-junior-1408a7192/)
[![Blog](https://img.shields.io/badge/Instagram-E4405F?style=for-the-badge&logo=instagram&logoColor=white)](https://instagram.com/braz_juniior?igshid=MzMyNGUyNmU2YQ==)

 #### Ainda estou aprendendo...

![Braizera GitHub stats](https://github-readme-stats.vercel.app/api?username=Braizera&show_icons=true&theme=radical)

## Tecnologias que estou aprendendo

<div style="display: inline_block"><br/>
  <img align="center" alt="html5" src="https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white" />
  <img align="center" alt="html5" src="https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white" />
  <img align="center" alt="html5" src="https://img.shields.io/badge/JavaScript-323330?style=for-the-badge&logo=javascript&logoColor=F7DF1E" />
   <img align="center" alt="html5" src="https://img.shields.io/badge/Python-14354C?style=for-the-badge&logo=python&logoColor=white" />
</div><br/>

Entusiasta por tecnologia, apaixonado por inovação! Estudante de Sistema de Informação em busca de conhecimento e oportunidades para contribuir em projetos empolgantes. Amante de programação, design e desenvolvimento web. Sempre pronto para aprender e colaborar!


<!---
Braizera/Braizera is a ✨ special ✨ repository because its `README.md` (this file) appears on your GitHub profile.
You can click the Preview link to take a look at your changes.
--->

## Script de desativação em massa (DEXBoard)

Criei o script `scripts/desativar_usuarios_dexboard.py` para desativar usuários em lote via API.

### Exemplo de CSV

```csv
user_id,email
123,
,usuario1@empresa.com
456,usuario2@empresa.com
```

### Execução (simulação)

```bash
python3 scripts/desativar_usuarios_dexboard.py \
  --base-url "https://seu-dexboard.com" \
  --token "SEU_TOKEN" \
  --input "usuarios.csv" \
  --id-column "user_id" \
  --email-column "email" \
  --dry-run
```

### Execução real

```bash
python3 scripts/desativar_usuarios_dexboard.py \
  --base-url "https://seu-dexboard.com" \
  --token "SEU_TOKEN" \
  --input "usuarios.csv"
```

> Ajuste os parâmetros `--lookup-endpoint`, `--deactivate-endpoint` e `--deactivate-payload` conforme o contrato da API do seu DEXBoard.
