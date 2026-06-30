import { NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { db } from '@/lib/db';

export async function POST(request: Request) {
  try {
    const { employeeId } = await request.json();

    if (!employeeId) {
      return NextResponse.json({ success: false, error: 'Employee ID is required' }, { status: 400 });
    }

    let employeeData: any = null;
    let role = 'Employee';

    // Simulated Finance ID for testing since it's not in the default employees list
    if (employeeId.toUpperCase() === 'FIN-001') {
      employeeData = {
        employee_id: 'FIN-001',
        name: 'Finance User',
        designation: 'Finance Specialist',
        department: 'Finance',
      };
      role = 'Finance';
    } else {
      // Look up in Firestore
      const doc = await db.collection('employees').doc(employeeId).get();
      if (!doc.exists) {
        return NextResponse.json({ success: false, error: 'Employee not found' }, { status: 404 });
      }
      employeeData = doc.data();

      const designation = (employeeData.designation || '').toLowerCase();
      const department = (employeeData.department || '').toLowerCase();

      if (designation.includes('manager')) {
        role = 'Manager';
      } else if (designation.includes('finance') || department.includes('finance')) {
        role = 'Finance';
      } else {
        return NextResponse.json({ 
          success: false, 
          error: 'Access Denied: Only Managers and Finance Team can access this portal.' 
        }, { status: 403 });
      }
    }

    // Set 10-minute session cookie
    const sessionData = {
      employeeId: employeeData.employee_id,
      name: employeeData.name,
      role: role,
      designation: employeeData.designation,
      department: employeeData.department,
      expiresAt: Date.now() + 10 * 60 * 1000 // 10 minutes from now
    };

    const cookieStore = await cookies();
    cookieStore.set('session', JSON.stringify(sessionData), {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict',
      maxAge: 10 * 60, // 10 minutes in seconds
      path: '/'
    });

    return NextResponse.json({ success: true, user: sessionData });
  } catch (error: any) {
    console.error('Login error:', error);
    return NextResponse.json({ success: false, error: 'Internal Server Error' }, { status: 500 });
  }
}
