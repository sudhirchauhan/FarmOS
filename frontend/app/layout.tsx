import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = { title: 'FarmOS · Planning', description: 'Weekly farm planning with transparent assumptions.' };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
