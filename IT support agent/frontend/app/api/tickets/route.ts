import { NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { db } from '@/lib/db';

export async function GET() {
  try {
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

    const { employeeId, role } = session;
    let tickets: any[] = [];

    if (role === 'Manager') {
      // Query tickets where this manager is the manager of the requester
      const snapshot = await db.collection('tickets')
        .where('requester.manager', '==', employeeId)
        .get();
      
      snapshot.forEach((doc: any) => {
        tickets.push(doc.data());
      });
    } else if (role === 'Finance') {
      // Query all tickets for Finance
      const snapshot = await db.collection('tickets').get();
      snapshot.forEach((doc: any) => {
        tickets.push(doc.data());
      });
    }

    // Sort by created_at descending
    tickets.sort((a, b) => {
      const dateA = new Date(a.created_at || 0).getTime();
      const dateB = new Date(b.created_at || 0).getTime();
      return dateB - dateA;
    });

    return NextResponse.json({ success: true, tickets });
  } catch (error: any) {
    console.error('Fetch tickets error:', error);
    return NextResponse.json({ success: false, error: 'Internal Server Error' }, { status: 500 });
  }
}
