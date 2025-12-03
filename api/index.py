# -*- coding: utf-8 -*-
from flask import Flask, request, render_template_string
from datetime import datetime, timedelta

app = Flask(__name__)

valid_operations = [
    "Autre HNO",
    "Insertion NRA",
    "Installation d'un DSLAM mobile",
    "Installation/migration/mise en prod d'un switch",
    "Intervention sur alimentation d'un switch",
    "Migration/ajout bandeau NRJ",
    "Normalisation/vérification/maintenance sur un NRA",
    "Shunt d'un départ NRJ",
    "Suppression switch"
]

valid_intervenants = [
    "FONTAINE Rodolphe (PQIS)",
    "RIZZO Anthony (CQIS)",
    "JULIEN Williams (PDEM)",
    "PEREIRA David (PDEM)",
    "GONNORD Bertrand (CDEM)",
    "AUGE Ludovic (CDEM)",
    "BURG Fabien (CDEM)",
    "DEVLIN Christophe (CDEM)",
    "KHERBOUCHE Zoubir (CDEM)"
]

@app.route('/', methods=['GET', 'POST'])
def form():
    form_data = None
    if request.method == 'POST':
        type_operation = request.form.get('type_operation')
        date_input = request.form.get('date')
        try:
            date_obj = datetime.strptime(date_input, "%d/%m/%Y")
            date_str = f"Dans la nuit du {date_obj.strftime('%d/%m/%Y')} au {(date_obj + timedelta(days=1)).strftime('%d/%m/%Y')}"
        except ValueError:
            date_str = "Date invalide"

        details = request.form.get('details')
        sites = request.form.get('sites').upper()
        impact = request.form.get('impact') or "Aucun impact"
        intervenants = request.form.get('intervenants')
        deuxieme_intervenant = request.form.get('deuxieme_intervenant') or "-"

        form_data = f"""Type d'opération : {type_operation}
Date : {date_str}
Détail : {details}
Site(s) concerné(s) : {sites}
Impact : {impact}
Intervenants : {intervenants}
Deuxième intervenant : {deuxieme_intervenant}"""

    ops_html = "".join([f'<option value="{op}">{op}</option>' for op in valid_operations])
    intervenants_html = "".join([f'<option value="{i}">{i}</option>' for i in valid_intervenants])

    form_template = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Formulaire d'Intervention Technique</title>
    <script src="https://cdn.tailwindcss.com"><\/script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap');
        body {{ font-family: 'Inter', sans-serif; background-color: #f7f9fb; }}
        select:focus, input:focus, textarea:focus {{
            border-color: #E80029 !important;
            box-shadow: 0 0 0 3px rgba(232, 0, 41, 0.1) !important;
        }}
    </style>
    <script>
        function copyToClipboard() {{
            const content = document.getElementById("generatedForm").textContent;
            navigator.clipboard.writeText(content).then(() => {{
                const msg = document.getElementById("copyMessage");
                msg.style.opacity = '1';
                setTimeout(() => {{ msg.style.opacity = '0'; }}, 2000);
            }}).catch(() => alert("Erreur lors de la copie"));
        }}
    </script>
</head>
<body class="p-4 sm:p-8">
    <div class="max-w-4xl mx-auto bg-white shadow-xl rounded-xl p-6 sm:p-10">
        <header class="mb-8 border-b pb-4 border-gray-200">
            <h1 class="text-3xl font-extrabold" style="color: #E80029;">🔴 Formulaire d'Opération Technique</h1>
            <p class="text-gray-500 mt-1">Saisissez les détails pour générer le rapport d'opération standardisé.</p>
        </header>

        <form method="POST" class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="md:col-span-2">
                <label class="block text-sm font-medium text-gray-700 mb-1">Type d'opération <span class="text-red-500">*</span></label>
                <select name="type_operation" required class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm">
                    <option value="">-- Sélectionner une opération --</option>
                    {ops_html}
                </select>
            </div>

            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Date (DD/MM/YYYY) <span class="text-red-500">*</span></label>
                <input type="text" name="date" placeholder="Ex: 05/12/2025" required class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm">
            </div>

            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Site(s) concerné(s) <span class="text-red-500">*</span></label>
                <input type="text" name="sites" placeholder="Ex: CND75, PARD12..." required class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm">
            </div>

            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Intervenant Principal <span class="text-red-500">*</span></label>
                <select name="intervenants" required class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm">
                    <option value="">-- Sélectionner un intervenant --</option>
                    {intervenants_html}
                </select>
            </div>

            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Deuxième intervenant</label>
                <select name="deuxieme_intervenant" class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm">
                    <option value="">-- Optionnel --</option>
                    {intervenants_html}
                </select>
            </div>

            <div class="md:col-span-2">
                <label class="block text-sm font-medium text-gray-700 mb-1">Détail de l'opération <span class="text-red-500">*</span></label>
                <textarea name="details" rows="4" placeholder="Description complète de l'intervention..." required class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm"></textarea>
            </div>

            <div class="md:col-span-2">
                <label class="block text-sm font-medium text-gray-700 mb-1">Impact (laisser vide = "Aucun impact")</label>
                <input type="text" name="impact" placeholder="Ex: Coupure de X minutes..." class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm">
            </div>

            <div class="md:col-span-2 mt-4">
                <button type="submit" class="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-md text-lg font-medium text-white transition duration-200" style="background-color: #E80029;" onmouseover="this.style.backgroundColor='#c40022'" onmouseout="this.style.backgroundColor='#E80029'">
                    Générer et Afficher le Formulaire
                </button>
            </div>
        </form>

        {'<div class="mt-12 pt-6 border-t border-gray-200"><h2 class="text-2xl font-bold text-gray-800 mb-4">📝 Résultat du Formulaire</h2><pre id="generatedForm" class="whitespace-pre-wrap p-4 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-700 leading-relaxed">' + form_data + '</pre><button onclick="copyToClipboard()" class="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-green-600 hover:bg-green-700"><span>📋 Copier le formulaire</span></button><span id="copyMessage" class="ml-4 text-sm text-green-600" style="opacity: 0; transition: opacity 0.3s;">Copié !</span></div>' if form_data else ''}
    </div>
</body>
</html>"""

    return render_template_string(form_template)

if __name__ == '__main__':
    app.run(debug=False)
