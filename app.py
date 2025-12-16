from flask import Flask, render_template, request, redirect, url_for, flash
from final_project_db import get_connection

app = Flask(__name__)
app.secret_key = "change-this-key"  # needed for flash messages


# -----------------------------------------
# HRM: Employees (LIST)
# -----------------------------------------
@app.route("/hrm/employees")
def hrm_employees_list():
    show = request.args.get("show", "active")  # active | all

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    where_clause = ""
    params = []

    if show == "active":
        where_clause = "WHERE e.is_active = %s"
        params.append(1)

    query = f"""
        SELECT
            e.employee_id,
            e.employee_number,
            e.first_name,
            e.last_name,
            e.email,
            e.phone,
            e.hire_date,
            e.is_active,
            d.department_name,
            j.title_name
        FROM employees e
        JOIN departments d ON e.department_id = d.department_id
        JOIN job_titles j ON e.job_title_id = j.job_title_id
        {where_clause}
        ORDER BY e.last_name, e.first_name
    """

    cur.execute(query, params)
    employees = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "hrm/employees_list.html",
        employees=employees,
        show=show
    )


# -----------------------------------------
# HRM: Employees (ADD)
# -----------------------------------------
@app.route("/hrm/employees/add", methods=["GET", "POST"])
def hrm_employee_add():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # dropdown data
    cur.execute("SELECT department_id, department_name FROM departments WHERE is_active = 1 ORDER BY department_name;")
    departments = cur.fetchall()

    cur.execute("SELECT job_title_id, title_name FROM job_titles WHERE is_active = 1 ORDER BY title_name;")
    job_titles = cur.fetchall()

    if request.method == "POST":
        employee_number = request.form["employee_number"].strip()
        first_name = request.form["first_name"].strip()
        last_name = request.form["last_name"].strip()
        email = request.form["email"].strip()
        phone = request.form.get("phone", "").strip() or None
        hire_date = request.form["hire_date"]
        department_id = int(request.form["department_id"])
        job_title_id = int(request.form["job_title_id"])

        try:
            cur.execute("""
                INSERT INTO employees
                (employee_number, first_name, last_name, email, phone, hire_date, department_id, job_title_id, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1)
            """, (employee_number, first_name, last_name, email, phone, hire_date, department_id, job_title_id))
            conn.commit()
            flash("Employee added successfully.", "success")
            return redirect(url_for("hrm_employees_list"))
        except Exception as e:
            conn.rollback()
            error_msg = str(e)

            if "employee_number" in error_msg:
                flash("Employee number already exists. Please enter a unique employee number.", "warning")
            elif "email" in error_msg:
                flash("Email address already exists. Please use a different email.", "warning")
            else:
                flash("An unexpected database error occurred.", "danger")

    cur.close()
    conn.close()
    return render_template("hrm/employee_form.html", mode="add", employee=None,
                           departments=departments, job_titles=job_titles)


# -----------------------------------------
# HRM: Employees (EDIT)
# -----------------------------------------
@app.route("/hrm/employees/<int:employee_id>/edit", methods=["GET", "POST"])
def hrm_employee_edit(employee_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM employees WHERE employee_id = %s;", (employee_id,))
    employee = cur.fetchone()
    if not employee:
        cur.close()
        conn.close()
        flash("Employee not found.", "warning")
        return redirect(url_for("hrm_employees_list"))

    # dropdown data
    cur.execute("SELECT department_id, department_name FROM departments WHERE is_active = 1 ORDER BY department_name;")
    departments = cur.fetchall()

    cur.execute("SELECT job_title_id, title_name FROM job_titles WHERE is_active = 1 ORDER BY title_name;")
    job_titles = cur.fetchall()

    if request.method == "POST":
        employee_number = request.form["employee_number"].strip()
        first_name = request.form["first_name"].strip()
        last_name = request.form["last_name"].strip()
        email = request.form["email"].strip()
        phone = request.form.get("phone", "").strip() or None
        hire_date = request.form["hire_date"]
        department_id = int(request.form["department_id"])
        job_title_id = int(request.form["job_title_id"])
        is_active = 1 if request.form.get("is_active") == "1" else 0

        try:
            cur.execute("""
                UPDATE employees
                SET employee_number=%s,
                    first_name=%s,
                    last_name=%s,
                    email=%s,
                    phone=%s,
                    hire_date=%s,
                    department_id=%s,
                    job_title_id=%s,
                    is_active=%s
                WHERE employee_id=%s
            """, (employee_number, first_name, last_name, email, phone, hire_date,
                  department_id, job_title_id, is_active, employee_id))
            conn.commit()
            flash("Employee updated successfully.", "success")
            return redirect(url_for("hrm_employees_list"))
        except Exception as e:
            conn.rollback()
            flash(f"Error updating employee: {e}", "danger")

    cur.close()
    conn.close()
    return render_template("hrm/employee_form.html", mode="edit", employee=employee,
                           departments=departments, job_titles=job_titles)


# -----------------------------------------
# HRM: Employees (DISABLE / SOFT DELETE)
# -----------------------------------------
@app.route("/hrm/employees/<int:employee_id>/disable", methods=["POST"])
def hrm_employee_disable(employee_id):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("UPDATE employees SET is_active = 0 WHERE employee_id = %s;", (employee_id,))
        conn.commit()
        flash("Employee disabled (soft delete).", "info")
    except Exception as e:
        conn.rollback()
        flash(f"Error disabling employee: {e}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("hrm_employees_list"))


# =========================================================
# PM: Clients (LIST)
# =========================================================
@app.route("/pm/clients")
def pm_clients_list():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    show = request.args.get("show", "active")  # active | all
    where_clause = ""
    params = []
    if show == "active":
        where_clause = "WHERE is_active = %s"
        params.append(1)

    cur.execute(f"""
        SELECT client_id, client_name, contact_name, contact_email, contact_phone, is_active, created_at
        FROM clients
        {where_clause}
        ORDER BY client_name
    """, params)
    clients = cur.fetchall()

    cur.close()
    conn.close()
    return render_template("pm/clients_list.html", clients=clients, show=show)


# =========================================================
# PM: Clients (ADD)
# =========================================================
@app.route("/pm/clients/add", methods=["GET", "POST"])
def pm_client_add():
    if request.method == "POST":
        client_name = request.form["client_name"].strip()
        contact_name = request.form.get("contact_name", "").strip() or None
        contact_email = request.form.get("contact_email", "").strip() or None
        contact_phone = request.form.get("contact_phone", "").strip() or None

        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO clients (client_name, contact_name, contact_email, contact_phone, is_active)
                VALUES (%s, %s, %s, %s, 1)
            """, (client_name, contact_name, contact_email, contact_phone))
            conn.commit()
            flash("Client created successfully.", "success")
            return redirect(url_for("pm_clients_list"))
        except Exception as e:
            conn.rollback()
            msg = str(e)
            if "Duplicate" in msg and "client_name" in msg:
                flash("Client name already exists. Please choose a unique name.", "warning")
            else:
                flash(f"Error creating client: {e}", "danger")
        finally:
            cur.close()
            conn.close()

    return render_template("pm/client_form.html", mode="add", client=None)


# =========================================================
# PM: Clients (EDIT)
# =========================================================
@app.route("/pm/clients/<int:client_id>/edit", methods=["GET", "POST"])
def pm_client_edit(client_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM clients WHERE client_id = %s;", (client_id,))
    client = cur.fetchone()
    if not client:
        cur.close(); conn.close()
        flash("Client not found.", "warning")
        return redirect(url_for("pm_clients_list"))

    if request.method == "POST":
        client_name = request.form["client_name"].strip()
        contact_name = request.form.get("contact_name", "").strip() or None
        contact_email = request.form.get("contact_email", "").strip() or None
        contact_phone = request.form.get("contact_phone", "").strip() or None
        is_active = 1 if request.form.get("is_active") == "1" else 0

        try:
            cur.execute("""
                UPDATE clients
                SET client_name=%s, contact_name=%s, contact_email=%s, contact_phone=%s, is_active=%s
                WHERE client_id=%s
            """, (client_name, contact_name, contact_email, contact_phone, is_active, client_id))
            conn.commit()
            flash("Client updated successfully.", "success")
            return redirect(url_for("pm_clients_list"))
        except Exception as e:
            conn.rollback()
            msg = str(e)
            if "Duplicate" in msg and "client_name" in msg:
                flash("Client name already exists. Please choose a unique name.", "warning")
            else:
                flash(f"Error updating client: {e}", "danger")

    cur.close(); conn.close()
    return render_template("pm/client_form.html", mode="edit", client=client)


# =========================================================
# PM: Clients (DISABLE / SOFT DELETE)
# =========================================================
@app.route("/pm/clients/<int:client_id>/disable", methods=["POST"])
def pm_client_disable(client_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE clients SET is_active = 0 WHERE client_id = %s;", (client_id,))
        conn.commit()
        flash("Client disabled (soft delete).", "info")
    except Exception as e:
        conn.rollback()
        flash(f"Error disabling client: {e}", "danger")
    finally:
        cur.close(); conn.close()
    return redirect(url_for("pm_clients_list"))


# =========================================================
# PM: Projects (LIST)
# =========================================================
@app.route("/pm/projects")
def pm_projects_list():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    show = request.args.get("show", "active")  # active | all
    where_clause = ""
    params = []
    if show == "active":
        where_clause = "WHERE p.is_active = %s"
        params.append(1)

    cur.execute(f"""
        SELECT
            p.project_id, p.project_code, p.project_name, p.start_date, p.end_date, p.status, p.is_active,
            c.client_name
        FROM projects p
        JOIN clients c ON p.client_id = c.client_id
        {where_clause}
        ORDER BY p.project_code
    """, params)
    projects = cur.fetchall()

    cur.close(); conn.close()
    return render_template("pm/projects_list.html", projects=projects, show=show)


# =========================================================
# PM: Projects (ADD)
# =========================================================
@app.route("/pm/projects/add", methods=["GET", "POST"])
def pm_project_add():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT client_id, client_name FROM clients WHERE is_active=1 ORDER BY client_name;")
    clients = cur.fetchall()

    if request.method == "POST":
        client_id = int(request.form["client_id"])
        project_code = request.form["project_code"].strip()
        project_name = request.form["project_name"].strip()
        start_date = request.form["start_date"]
        end_date = request.form.get("end_date", "").strip() or None
        status = request.form.get("status", "Active").strip()

        try:
            cur.execute("""
                INSERT INTO projects (client_id, project_code, project_name, start_date, end_date, status, is_active)
                VALUES (%s,%s,%s,%s,%s,%s,1)
            """, (client_id, project_code, project_name, start_date, end_date, status))
            conn.commit()
            flash("Project created successfully.", "success")
            return redirect(url_for("pm_projects_list"))
        except Exception as e:
            conn.rollback()
            msg = str(e)
            if "Duplicate" in msg and "project_code" in msg:
                flash("Project code already exists. Please use a unique project code.", "warning")
            else:
                flash(f"Error creating project: {e}", "danger")

    cur.close(); conn.close()
    return render_template("pm/project_form.html", mode="add", project=None, clients=clients)


# =========================================================
# PM: Projects (EDIT)
# =========================================================
@app.route("/pm/projects/<int:project_id>/edit", methods=["GET", "POST"])
def pm_project_edit(project_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM projects WHERE project_id=%s;", (project_id,))
    project = cur.fetchone()
    if not project:
        cur.close(); conn.close()
        flash("Project not found.", "warning")
        return redirect(url_for("pm_projects_list"))

    cur.execute("SELECT client_id, client_name FROM clients WHERE is_active=1 ORDER BY client_name;")
    clients = cur.fetchall()

    if request.method == "POST":
        client_id = int(request.form["client_id"])
        project_code = request.form["project_code"].strip()
        project_name = request.form["project_name"].strip()
        start_date = request.form["start_date"]
        end_date = request.form.get("end_date", "").strip() or None
        status = request.form.get("status", "Active").strip()
        is_active = 1 if request.form.get("is_active") == "1" else 0

        try:
            cur.execute("""
                UPDATE projects
                SET client_id=%s, project_code=%s, project_name=%s,
                    start_date=%s, end_date=%s, status=%s, is_active=%s
                WHERE project_id=%s
            """, (client_id, project_code, project_name, start_date, end_date, status, is_active, project_id))
            conn.commit()
            flash("Project updated successfully.", "success")
            return redirect(url_for("pm_projects_list"))
        except Exception as e:
            conn.rollback()
            msg = str(e)
            if "Duplicate" in msg and "project_code" in msg:
                flash("Project code already exists. Please use a unique project code.", "warning")
            else:
                flash(f"Error updating project: {e}", "danger")

    cur.close(); conn.close()
    return render_template("pm/project_form.html", mode="edit", project=project, clients=clients)


# =========================================================
# PM: Projects (DISABLE / SOFT DELETE)
# =========================================================
@app.route("/pm/projects/<int:project_id>/disable", methods=["POST"])
def pm_project_disable(project_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE projects SET is_active = 0 WHERE project_id = %s;", (project_id,))
        conn.commit()
        flash("Project disabled (soft delete).", "info")
    except Exception as e:
        conn.rollback()
        flash(f"Error disabling project: {e}", "danger")
    finally:
        cur.close(); conn.close()
    return redirect(url_for("pm_projects_list"))


# =========================================================
# PM: Project Members (ASSIGN/REMOVE)
# =========================================================
@app.route("/pm/projects/<int:project_id>/members", methods=["GET", "POST"])
def pm_project_members(project_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # Project header
    cur.execute("""
        SELECT p.project_id, p.project_code, p.project_name, c.client_name
        FROM projects p
        JOIN clients c ON p.client_id = c.client_id
        WHERE p.project_id=%s
    """, (project_id,))
    project = cur.fetchone()
    if not project:
        cur.close(); conn.close()
        flash("Project not found.", "warning")
        return redirect(url_for("pm_projects_list"))

    # Current members
    cur.execute("""
        SELECT e.employee_id, e.employee_number, e.first_name, e.last_name
        FROM project_members pm
        JOIN employees e ON pm.employee_id = e.employee_id
        WHERE pm.project_id = %s
        ORDER BY e.last_name, e.first_name
    """, (project_id,))
    members = cur.fetchall()

    # Available employees to assign (active employees)
    cur.execute("""
        SELECT employee_id, employee_number, first_name, last_name
        FROM employees
        WHERE is_active = 1
        ORDER BY last_name, first_name
    """)
    employees = cur.fetchall()

    if request.method == "POST":
        employee_id = int(request.form["employee_id"])
        try:
            cur.execute("""
                INSERT INTO project_members (project_id, employee_id)
                VALUES (%s, %s)
            """, (project_id, employee_id))
            conn.commit()
            flash("Employee assigned to project.", "success")
            return redirect(url_for("pm_project_members", project_id=project_id))
        except Exception as e:
            conn.rollback()
            # Duplicate assignment is blocked by PRIMARY KEY(project_id, employee_id)
            msg = str(e)
            if "Duplicate" in msg:
                flash("That employee is already assigned to this project.", "warning")
            else:
                flash(f"Error assigning employee: {e}", "danger")

    cur.close(); conn.close()
    return render_template("pm/project_members.html", project=project, members=members, employees=employees)


@app.route("/pm/projects/<int:project_id>/members/<int:employee_id>/remove", methods=["POST"])
def pm_project_member_remove(project_id, employee_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            DELETE FROM project_members
            WHERE project_id=%s AND employee_id=%s
        """, (project_id, employee_id))
        conn.commit()
        flash("Employee removed from project.", "info")
    except Exception as e:
        conn.rollback()
        flash(f"Error removing member: {e}", "danger")
    finally:
        cur.close(); conn.close()
    return redirect(url_for("pm_project_members", project_id=project_id))


# =========================================================
# PM: Tasks (LIST)
# =========================================================
@app.route("/pm/tasks")
def pm_tasks_list():
    project_id = request.args.get("project_id", type=int)

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # Dropdown of projects
    cur.execute("SELECT project_id, project_code, project_name FROM projects WHERE is_active=1 ORDER BY project_code;")
    projects = cur.fetchall()

    params = []
    where_parts = []
    if project_id:
        where_parts.append("t.project_id = %s")
        params.append(project_id)

    # Show only active tasks by default
    show = request.args.get("show", "active")  # active | all
    if show == "active":
        where_parts.append("t.is_active = %s")
        params.append(1)

    where_clause = ""
    if where_parts:
        where_clause = "WHERE " + " AND ".join(where_parts)

    cur.execute(f"""
        SELECT
            t.task_id, t.task_name, t.task_status, t.due_date, t.is_active,
            p.project_code, p.project_name,
            e.first_name, e.last_name
        FROM tasks t
        JOIN projects p ON t.project_id = p.project_id
        LEFT JOIN employees e ON t.employee_id = e.employee_id
        {where_clause}
        ORDER BY p.project_code, t.due_date IS NULL, t.due_date, t.task_name
    """, params)
    tasks = cur.fetchall()

    cur.close(); conn.close()
    return render_template("pm/tasks_list.html", tasks=tasks, projects=projects, project_id=project_id, show=show)


# =========================================================
# PM: Tasks (ADD)
# =========================================================
@app.route("/pm/tasks/add", methods=["GET", "POST"])
def pm_task_add():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT project_id, project_code, project_name FROM projects WHERE is_active=1 ORDER BY project_code;")
    projects = cur.fetchall()

    cur.execute("""
        SELECT employee_id, employee_number, first_name, last_name
        FROM employees
        WHERE is_active=1
        ORDER BY last_name, first_name
    """)
    employees = cur.fetchall()

    if request.method == "POST":
        project_id = int(request.form["project_id"])
        employee_id_raw = request.form.get("employee_id", "").strip()
        employee_id = int(employee_id_raw) if employee_id_raw else None
        task_name = request.form["task_name"].strip()
        task_status = request.form.get("task_status", "To Do").strip()
        due_date = request.form.get("due_date", "").strip() or None

        try:
            cur.execute("""
                INSERT INTO tasks (project_id, employee_id, task_name, task_status, due_date, is_active)
                VALUES (%s,%s,%s,%s,%s,1)
            """, (project_id, employee_id, task_name, task_status, due_date))
            conn.commit()
            flash("Task created successfully.", "success")
            return redirect(url_for("pm_tasks_list", project_id=project_id))
        except Exception as e:
            conn.rollback()
            flash(f"Error creating task: {e}", "danger")

    cur.close(); conn.close()
    return render_template("pm/task_form.html", mode="add", task=None, projects=projects, employees=employees)


# =========================================================
# PM: Tasks (EDIT)
# =========================================================
@app.route("/pm/tasks/<int:task_id>/edit", methods=["GET", "POST"])
def pm_task_edit(task_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM tasks WHERE task_id=%s;", (task_id,))
    task = cur.fetchone()
    if not task:
        cur.close(); conn.close()
        flash("Task not found.", "warning")
        return redirect(url_for("pm_tasks_list"))

    cur.execute("SELECT project_id, project_code, project_name FROM projects WHERE is_active=1 ORDER BY project_code;")
    projects = cur.fetchall()

    cur.execute("""
        SELECT employee_id, employee_number, first_name, last_name
        FROM employees
        WHERE is_active=1
        ORDER BY last_name, first_name
    """)
    employees = cur.fetchall()

    if request.method == "POST":
        project_id = int(request.form["project_id"])
        employee_id_raw = request.form.get("employee_id", "").strip()
        employee_id = int(employee_id_raw) if employee_id_raw else None
        task_name = request.form["task_name"].strip()
        task_status = request.form.get("task_status", "To Do").strip()
        due_date = request.form.get("due_date", "").strip() or None
        is_active = 1 if request.form.get("is_active") == "1" else 0

        try:
            cur.execute("""
                UPDATE tasks
                SET project_id=%s, employee_id=%s, task_name=%s, task_status=%s,
                    due_date=%s, is_active=%s
                WHERE task_id=%s
            """, (project_id, employee_id, task_name, task_status, due_date, is_active, task_id))
            conn.commit()
            flash("Task updated successfully.", "success")
            return redirect(url_for("pm_tasks_list", project_id=project_id))
        except Exception as e:
            conn.rollback()
            flash(f"Error updating task: {e}", "danger")

    cur.close(); conn.close()
    return render_template("pm/task_form.html", mode="edit", task=task, projects=projects, employees=employees)


# =========================================================
# PM: Tasks (DISABLE / SOFT DELETE)
# =========================================================
@app.route("/pm/tasks/<int:task_id>/disable", methods=["POST"])
def pm_task_disable(task_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE tasks SET is_active = 0 WHERE task_id = %s;", (task_id,))
        conn.commit()
        flash("Task disabled (soft delete).", "info")
    except Exception as e:
        conn.rollback()
        flash(f"Error disabling task: {e}", "danger")
    finally:
        cur.close(); conn.close()
    return redirect(request.referrer or url_for("pm_tasks_list"))


# Home redirect
@app.route("/")
def home():
    return redirect(url_for("hrm_employees_list"))


if __name__ == "__main__":
    app.run(debug=True)
