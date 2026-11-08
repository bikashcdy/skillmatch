"""Application e-mails: decisions, strong matches and recruiter messages."""

from core.mail import SITE_URL, _sender, send

STRONG_MATCH = 70.0  # tell the recruiter


def _from_recruiter(job):
    """Show the recruiter's company as the sender; replies go to the recruiter's own email."""
    rec = job.recruiter
    name = (job.company or rec.company_name or rec.username).replace('"', "").replace("<", "").replace(">", "")
    address = _sender().split("<")[-1].rstrip(">")
    return f"{name} via JobMitra <{address}>", ([rec.email] if rec.email else None)


def application_decision(application):
    """Candidate: you were selected / not selected."""
    job, cand = application.job, application.candidate
    if application.status == "selected":
        subject = f"Good news: you were selected for {job.title}"
        body = (f"Hello {cand.username},\n\n{job.company} has selected you for the {job.title} position "
                f"({application.match_percentage}% match).\n")
    elif application.status == "rejected":
        subject = f"Update on your application: {job.title}"
        body = (f"Hello {cand.username},\n\nThank you for applying to {job.title} at {job.company}. "
                "They decided not to move forward this time. Check your Career plan for skills that can "
                "raise your match for similar jobs.\n")
    else:
        return False
    if application.recruiter_note:
        body += f"\nMessage from the recruiter:\n\"{application.recruiter_note}\"\n"
    sender, reply = _from_recruiter(job)
    body += (f"\nYou can reply to this email to reach {job.company} directly"
             f"{' (' + job.recruiter.email + ')' if job.recruiter.email else ''}.\n"
             f"Open your applications: {SITE_URL}/my-applications\n\n- {job.company} via JobMitra")
    return send(cand.email, subject, body, sender, reply)


def strong_matches(applications):
    """Recruiters: ONE email per recruiter listing every strong candidate (70%+) from this action."""
    by_recruiter = {}
    for app in applications:
        if app.match_percentage >= STRONG_MATCH:
            by_recruiter.setdefault(app.job.recruiter, []).append(app)
    sent = 0
    for rec, apps in by_recruiter.items():
        cand = apps[0].candidate
        lines = "\n".join(
            f"- {a.job.title}: {a.match_percentage}% (matched: {', '.join(a.matched_skills) or '-'})  {SITE_URL}/recruiter/jobs/{a.job_id}"
            for a in apps
        )
        body = (f"Hello {rec.username},\n\n{cand.username} applied with a strong match ({STRONG_MATCH:.0f}%+) to "
                f"{'your job' if len(apps) == 1 else str(len(apps)) + ' of your jobs'}:\n\n{lines}\n\n"
                f"Reply to this email to contact the candidate.\n\n- JobMitra")
        subject = (f"Strong match ({apps[0].match_percentage}%) for {apps[0].job.title}" if len(apps) == 1
                   else f"{len(apps)} strong matches from {cand.username}")
        sent += send(rec.email, subject, body, reply_to=[cand.email] if cand.email else None)
    return sent


def recruiter_message(application):
    """Candidate: the recruiter wrote you a note."""
    job, cand = application.job, application.candidate
    sender, reply = _from_recruiter(job)
    body = (f"Hello {cand.username},\n\n{job.company} sent you a message about {job.title}:\n\n"
            f"\"{application.recruiter_note}\"\n\nReply to this email to answer them directly.\n"
            f"See it here: {SITE_URL}/my-applications\n\n- {job.company} via JobMitra")
    return send(cand.email, f"New message from {job.company}", body, sender, reply)
