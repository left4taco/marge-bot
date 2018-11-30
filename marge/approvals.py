from . import gitlab
import logging as log

GET, POST, PUT = gitlab.GET, gitlab.POST, gitlab.PUT


class Approvals(gitlab.Resource):
    """Approval info for a MergeRequest."""

    def refetch_info(self):
        gitlab_version = self._api.version()
        if gitlab_version.release >= (9, 2, 2):
            approver_url = '/projects/{0.project_id}/merge_requests/{0.iid}/approvals'.format(self)
        else:
            # GitLab botched the v4 api before 9.2.3
            approver_url = '/projects/{0.project_id}/merge_requests/{0.id}/approvals'.format(self)

        if gitlab_version.is_ee:
            self._info = self._api.call(GET(approver_url))
        else:
            self._info = dict(self._info, approvals_left=0, approved_by=[])

    @property
    def iid(self):
        return self.info['iid']

    @property
    def project_id(self):
        return self.info['project_id']

    @property
    def approvals_left(self):
        return self.info['approvals_left'] or 0

    @property
    def sufficient(self):
        return not self.info['approvals_left']

    @property
    def approver_usernames(self):
        return [who['user']['username'] for who in self.info['approved_by']]

    @property
    def approver_ids(self):
        """Return the uids of the approvers."""
        return [who['user']['id'] for who in self.info['approved_by']]

    def reapprove(self):
        """Impersonates the approvers and re-approves the merge_request as them.

        The idea is that we want to get the approvers, push the rebased branch
        (which may invalidate approvals, depending on GitLab settings) and then
        restore the approval status.
        """
        if self._api.version().release >= (9, 2, 2):
            approve_url = '/projects/{0.project_id}/merge_requests/{0.iid}/approve'.format(self)
        else:
            # GitLab botched the v4 api before 9.2.3
            approve_url = '/projects/{0.project_id}/merge_requests/{0.id}/approve'.format(self)

        for uid in self.approver_ids:
            self._api.call(POST(approve_url), sudo=uid)

    def bot_approve(self):
        """Approve the MR. Usually called after rebase onto master locally and push the changes.
         In this case, the approvals get cleared.
        """
        log.info("Bot approve this MR.")
        if self._api.version().release >= (9, 2, 2):
            approve_url = '/projects/{0.project_id}/merge_requests/{0.iid}/approve'.format(self)
        else:
            # GitLab botched the v4 api before 9.2.3
            approve_url = '/projects/{0.project_id}/merge_requests/{0.id}/approve'.format(self)
        self._api.call(POST(approve_url))

