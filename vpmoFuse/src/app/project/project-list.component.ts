import { Component, OnInit } from '@angular/core';

import { IProject } from './project';
import { ProjectService } from './project.service';


@Component({
  selector: 'app-project-list',
  templateUrl: './project-list.component.html',
  styleUrls: ['./project-list.component.css']
})

export class ProjectListComponent implements OnInit {
  errorMessage: string;

  constructor(private _projectService: ProjectService) {}

  projects: IProject[] = [];

  ngOnInit(): void {
    console.log('In onInit');
    this._projectService.getProjects()
          .subscribe(
                projects => this.projects = projects,
                error => this.errorMessage = <any>error);
    }


  }
