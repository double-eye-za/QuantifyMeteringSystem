# Company Access Guide - double-eye-za

## For Organization Admins

### Quick Access Setup

1. **Give Everyone Read Access** (Recommended to start):
   - Go to: https://github.com/double-eye-za/QuantifyMeteringSystem/settings/access
   - Under "Manage access" → "Base role"
   - Select **"Read"** - everyone in double-eye-za can view
   - Click "Save"

2. **Create Teams**:
   Go to: https://github.com/orgs/double-eye-za/teams

   **Recommended Teams:**
   - `quantify-developers` - Write access (can push code)
   - `quantify-managers` - Admin access (full control)
   - `quantify-qa` - Write access (can create issues)
   - `quantify-viewers` - Read access (view only)

### For Team Members

## How to Access the Repository

### Step 1: Join GitHub
1. Create account at https://github.com (free)
2. Share your username with the organization admin

### Step 2: Accept Organization Invitation
1. Check your email for invitation from double-eye-za
2. Click "Accept invitation"
3. You're now part of the organization!

### Step 3: Access the Project
1. Go to: https://github.com/double-eye-za/QuantifyMeteringSystem
2. Click "Code" → Copy the URL
3. Clone to your computer:

```bash
# Using SSH (recommended)
git clone git@github.com:double-eye-za/QuantifyMeteringSystem.git

# Using HTTPS
git clone https://github.com/double-eye-za/QuantifyMeteringSystem.git
```

### Step 4: Start Working
```bash
# Enter project directory
cd QuantifyMeteringSystem

# View the prototype
open prototype/index.html  # Mac
start prototype/index.html # Windows

# Read documentation
open README.md
```

## Permission Levels Explained

| Level | Can View | Can Clone | Can Push | Can Merge | Can Delete |
|-------|----------|-----------|----------|-----------|------------|
| **Read** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Triage** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Write** | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Maintain** | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Admin** | ✅ | ✅ | ✅ | ✅ | ✅ |

## Who Needs What Access?

| Role | Recommended Permission | Why |
|------|----------------------|-----|
| **Developers** | Write | Push code, create branches |
| **QA/Testers** | Write | Create issues, test branches |
| **Project Managers** | Maintain | Manage issues, reviews |
| **Stakeholders** | Read | View progress, comment |
| **Admins/Leads** | Admin | Full control |

## Quick Links for Admins

### Manage Access
- Repository Access: https://github.com/double-eye-za/QuantifyMeteringSystem/settings/access
- Organization Teams: https://github.com/orgs/double-eye-za/teams
- Organization Members: https://github.com/orgs/double-eye-za/people
- Pending Invitations: https://github.com/orgs/double-eye-za/people/pending_invitations

### Add New Team Member
1. Go to: https://github.com/orgs/double-eye-za/people
2. Click "Invite member"
3. Enter email or GitHub username
4. Select teams they should join
5. Send invitation

## Security Best Practices

1. **Use Teams, Not Individual Access**
   - Easier to manage
   - Consistent permissions
   - Better audit trail

2. **Principle of Least Privilege**
   - Give minimum required access
   - Upgrade as needed
   - Review regularly

3. **Regular Access Reviews**
   - Check who has access monthly
   - Remove inactive members
   - Update team memberships

## For New Employees

### Getting Started Checklist
- [ ] Create GitHub account
- [ ] Share username with IT/Admin
- [ ] Accept organization invitation
- [ ] Clone repository
- [ ] Read TEAM_ONBOARDING.md
- [ ] Test prototype locally
- [ ] Join team chat/slack
- [ ] Attend project briefing

## Troubleshooting

### Can't See Repository?
- Check you're logged into GitHub
- Verify you accepted the invitation
- Contact organization admin

### Can't Push Code?
- Check your permission level (need Write)
- Verify you're on the right branch
- Ensure you've pulled latest changes

### Need Help?
1. Check this guide
2. Read TEAM_ONBOARDING.md
3. Contact organization admin
4. Create an issue in the repository

---

**Organization**: double-eye-za  
**Repository**: QuantifyMeteringSystem  
**URL**: https://github.com/double-eye-za/QuantifyMeteringSystem