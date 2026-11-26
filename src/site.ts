// Everything the team is likely to change lives here.
import type { ImageMetadata } from 'astro';
import fontys from './assets/images/torpedo/partners/fontys.png';
import knightec from './assets/images/torpedo/partners/knightec.svg';
import qtronic from './assets/images/torpedo/partners/q-tronic.svg';
import evEurope from './assets/images/torpedo/partners/ev-europe.svg';
import summa from './assets/images/torpedo/partners/summa.svg';
import tailorSteel from './assets/images/torpedo/partners/247tailorsteel.svg';
import { getPermalink } from './utils/permalinks';

export const contact = {
  email: 'torpedokid2021@gmail.com',
  instagram: 'https://www.instagram.com/torpedokid_fontys/',
  linkedin: 'https://www.linkedin.com/company/fontys-engineering-torpedokid/',
};

// Application form (Google Forms; applicants sign in so their email is recorded).
export const applyForm =
  'https://docs.google.com/forms/d/e/1FAIpQLSc4p8znoZhYt5e3m5y8SWBUHf52sX_6h8zfO-Xc7dvbm9TyLg/viewform';

export const mailto = (subject?: string) =>
  `mailto:${contact.email}${subject ? `?subject=${encodeURIComponent(subject)}` : ''}`;

// Leave `logo` out to show the name as text, and `href` out for no link.
// `height` is the largest logo height in rem, to balance wide and tall logos.
interface Partner {
  name: string;
  href?: string;
  logo?: ImageMetadata;
  height?: number;
}

export const partners: Partner[] = [
  {
    name: 'Fontys Technology',
    href: 'https://www.fontys.nl/en/About-Fontys/Fontys-Technology.htm',
    logo: fontys,
    height: 6,
  },
  { name: 'Knightec', href: 'https://www.knightecgroup.com/', logo: knightec, height: 4.75 },
  { name: 'Q-tronic', href: 'https://q-tronic.nl/', logo: qtronic, height: 2 },
  { name: 'EV Europe', href: 'https://eveurope.eu/', logo: evEurope, height: 2.5 },
  {
    name: 'Summa Automotive',
    href: 'https://summa-onderwijs.nl/en/schools/summa-automotive/',
    logo: summa,
    height: 3,
  },
  { name: '247TailorSteel', href: 'https://247tailorsteel.com/', logo: tailorSteel, height: 3.75 },
  { name: 'BatteryCenter' },
];

export const nav = [
  { text: 'Home', href: getPermalink('/') },
  { text: 'About', href: getPermalink('/about') },
  { text: 'Join us', href: getPermalink('/join-us') },
  { text: 'Partners', href: getPermalink('/partner-with-us') },
  { text: 'Contact', href: getPermalink('/contact') },
];

// Public-domain photo, Wikimedia Commons / DPLA.
export const photoSource =
  'https://commons.wikimedia.org/wiki/File:Glenville_Racetrack,_1903_-_DPLA_-_7e271322d07aac3d4b684fd1f7802b1b.jpg';
