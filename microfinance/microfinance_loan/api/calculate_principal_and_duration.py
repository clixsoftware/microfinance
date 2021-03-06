# -*- coding: utf-8 -*-
# Copyright (c) 2018, Libermatic and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt, add_months, add_days, getdate, today
from microfinance.microfinance_loan.utils \
    import get_billing_date, month_diff, interest

@frappe.whitelist()
def execute(income, loan_plan, end_date, execution_date=today()):
    '''
        Return a dict containing the maximum allowed principal along with the
        duration and monthly installment.

        :param income: Renumeration received by the Customer
        :param loan_plan: Name of a Loan Plan
        :param end_date: Maximum date on which the loan could end
        :param execution_date: Date on which the loan would start
    '''

    if isinstance(loan_plan, basestring):
        plan = frappe.get_doc('Loan Plan', loan_plan)
    elif isinstance(loan_plan, dict):
        plan = frappe._dict(loan_plan)
    else:
        frappe.throw('Invalid Loan Plan format', ValueError)

    if not plan.income_multiple or not plan.max_duration or not plan.billing_day:
        frappe.throw('Missing values in Loan Plan', ValueError)

    income_portion = flt(plan.income_multiple) / flt(plan.max_duration)
    recovery_amount = flt(income) * income_portion
    duration = plan.max_duration


    billing_start_date = get_billing_date(execution_date, plan.billing_day)
    expected_eta = add_months(billing_start_date, plan.max_duration)

    if not plan.force_duration and getdate(end_date) <= getdate(expected_eta):
        duration = month_diff(end_date, billing_start_date)
        expected_eta = add_months(get_billing_date(end_date, plan.billing_day), -1)

    principal = recovery_amount * duration

    return {
            'principal': principal,
            'expected_eta': add_days(expected_eta, -1),
            'duration': duration,
            'recovery_amount': recovery_amount,
            'initial_interest': interest(principal, plan.rate_of_interest, plan.calculation_slab),
        }
