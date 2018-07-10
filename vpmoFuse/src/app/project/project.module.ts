import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Routes } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import {platformBrowserDynamic} from '@angular/platform-browser-dynamic';

import { ProjectAddComponent } from './project-add.component';
import { ProjectService } from './project.service';
import { ProjectComponent } from './project.component';
import { MatDatepickerModule, MatNativeDateModule, MatFormFieldModule, MatIconModule, MatInputModule } from '@angular/material';
// import { MzButtonModule, MzInputModule, MzDatepickerModule } from 'ng2-materialize';

const ProjectRoutes: Routes = [
  {
      // path: 'project',
      // component: ProjectComponent,
      children: [
          { path: 'add', component: ProjectAddComponent },
      ]
  },
];

@NgModule({

  imports: [
    CommonModule,
    FormsModule,
    RouterModule.forChild([
      { path: 'Projectadd', component: ProjectAddComponent },
    ]),
    HttpClientModule,
    MatDatepickerModule,
    MatNativeDateModule,
    MatIconModule,
    MatFormFieldModule,
    MatInputModule,
  ],
  declarations: [
    ProjectComponent,
    ProjectAddComponent,
  ],
  providers: [
    ProjectService,
  ],
})
export class ProjectModule { }

platformBrowserDynamic().bootstrapModule(ProjectModule);
