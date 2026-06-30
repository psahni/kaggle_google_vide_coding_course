import { NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { db } from '@/lib/db';

export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const cookieStore = await cookies();
    const sessionCookie = cookieStore.get('session');

    if (!sessionCookie) {
      return NextResponse.json({ success: false, error: 'Unauthorized' }, { status: 401 });
    }

    const session = JSON.parse(sessionCookie.value);

    // Validate 10-minute expiry
    if (Date.now() > session.expiresAt) {
      cookieStore.delete('session');
      return NextResponse.json({ success: false, error: 'Session expired' }, { status: 401 });
    }

    const { employeeId, name, role } = session;
    const { action, reason, comment } = await request.json();

    const docRef = db.collection('tickets').doc(id);
    const doc = await docRef.get();

    if (!doc.exists) {
      return NextResponse.json({ success: false, error: 'Ticket not found' }, { status: 404 });
    }

    const ticket = doc.data() || {};
    const nowStr = new Date().toISOString();

    if (action === 'approve') {
      ticket.status = 'approved';
      ticket.approved_by = role.toLowerCase();
      
      const auditAction = role === 'Finance' ? 'finance_approved' : 'manager_approved';
      ticket.audit_trail.push({
        timestamp: nowStr,
        actor: role.toLowerCase(),
        action: auditAction,
        details: `Request approved by ${name} (${role}). Reason: ${reason || 'Approved via Web Portal'}`
      });
    } else if (action === 'reject') {
      ticket.status = 'rejected';
      
      const auditAction = role === 'Finance' ? 'finance_rejected' : 'manager_rejected';
      ticket.audit_trail.push({
        timestamp: nowStr,
        actor: role.toLowerCase(),
        action: auditAction,
        details: `Request rejected by ${name} (${role}). Reason: ${reason || 'Rejected via Web Portal'}`
      });
    } else if (action === 'comment') {
      if (!comment) {
        return NextResponse.json({ success: false, error: 'Comment content is required' }, { status: 400 });
      }
      ticket.audit_trail.push({
        timestamp: nowStr,
        actor: role.toLowerCase(),
        action: 'comment_added',
        details: `[Comment] ${name}: ${comment}`
      });
    } else {
      return NextResponse.json({ success: false, error: 'Invalid action' }, { status: 400 });
    }

    await docRef.set(ticket);

    return NextResponse.json({ success: true, ticket });
  } catch (error: any) {
    console.error('Update ticket error:', error);
    return NextResponse.json({ success: false, error: 'Internal Server Error' }, { status: 500 });
  }
}
