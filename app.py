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

form_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Formulaire d'Intervention</title>
    <script>
        function updateBackupOptions() {
            const intervenant = document.querySelector('select[name="intervenants"]').value;
            const backupSelect = document.querySelector('select[name="backup"]');
            let validBackups = [];

            if (intervenant === "FONTAINE Rodolphe (PQIS)") {
                validBackups = ["RIZZO Anthony (CQIS)"];
            } else if (intervenant === "RIZZO Anthony (CQIS)") {
                validBackups = ["FONTAINE Rodolphe (PQIS)"];
            } else {
                validBackups = {{ valid_intervenants | safe }}.filter(i => !i.includes("PQIS") && !i.includes("CQIS") && i !== intervenant);
            }

            backupSelect.innerHTML = validBackups.map(backup => `<option value="${backup}">${backup}</option>`).join('');
        }

        function copyToClipboard() {
            var content = document.getElementById("generatedForm").innerText;
            navigator.clipboard.writeText(content).then(function() {
                alert("Formulaire copié dans le presse-papiers !");
            }, function(err) {
                alert("Erreur lors de la copie : " + err);
            });
        }
    </script>
</head>
<body>
    <h1>Formulaire d'Intervention</h1>
    <form method="POST">
        <label for="type_operation">Type d'opération :</label>
        <select name="type_operation" required>
            {% for operation in valid_operations %}
            <option value="{{ operation }}">{{ operation }}</option>
            {% endfor %}
        </select><br><br>

        <label for="date">Date (DD/MM/YYYY) :</label>
        <input type="text" name="date" placeholder="28/01/2025" required><br><br>

        <label for="details">Détail :</label>
        <textarea name="details" placeholder="Description de l'intervention" required></textarea><br><br>

        <label for="sites">Site(s) concerné(s) :</label>
        <input type="text" name="sites" placeholder="LJU91" required><br><br>

        <label for="impact">Impact :</label>
        <input type="text" name="impact" placeholder="Aucun impact"><br><br>

        <label for="intervenants">Intervenants :</label>
        <select name="intervenants" onchange="updateBackupOptions()" required>
            {% for intervenant in valid_intervenants %}
            <option value="{{ intervenant }}">{{ intervenant }}</option>
            {% endfor %}
        </select><br><br>

        <label for="backup">Backup :</label>
        <select name="backup" required>
            {% for intervenant in valid_intervenants if intervenant != valid_intervenants[0] %}
            <option value="{{ intervenant }}">{{ intervenant }}</option>
            {% endfor %}
        </select><br><br>

        <button type="submit">Générer le formulaire</button>
    </form>

    {% if form_data %}
    <h2>Formulaire généré :</h2>
    <pre id="generatedForm">{{ form_data }}</pre>
    <button onclick="copyToClipboard()">Copier le formulaire</button>
    {% endif %}
</body>
</html>
"""

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
        backup = request.form.get('backup')

        form_data = f"""
Type d'opération : {type_operation}
Date : {date_str}
Détail : {details}
Site(s) concerné(s) : {sites}
Impact : {impact}
Intervenants : {intervenants}
Backup : {backup}
"""

    return render_template_string(
        form_template,
        valid_operations=valid_operations,
        valid_intervenants=valid_intervenants,
        form_data=form_data
    )

if __name__ == '__main__':
    app.run(debug=True)
